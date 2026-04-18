"""
Flask server: serves dashboard UI + REST API + starts bot in background thread.
"""

import os
import threading
import logging
from flask import Flask, jsonify, request, render_template_string
from state import BotState
from bot import start_bot
from dashboard import DASHBOARD_HTML, TRADING_HTML

log = logging.getLogger("server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)
state = BotState()
bot_thread = None

# Auto-start runs at module level so it works under gunicorn too
_auto_start = os.getenv("AUTO_START", "true").lower() == "true"
if _auto_start:
    log.info("AUTO_START=true — starting bot automatically")
    state.running = True
    bot_thread = threading.Thread(target=start_bot, args=(state,), daemon=True)
    bot_thread.start()


# ── API Routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/state")
def api_state():
    return jsonify(state.to_dict())


@app.route("/api/start", methods=["POST"])
def api_start():
    global bot_thread
    if state.running:
        return jsonify({"ok": False, "msg": "Already running"})
    state.running = True
    bot_thread = threading.Thread(target=start_bot, args=(state,), daemon=True)
    bot_thread.start()
    log.info("Bot started via API")
    return jsonify({"ok": True, "msg": "Bot started"})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    state.running = False
    log.info("Bot stopped via API")
    return jsonify({"ok": True, "msg": "Bot stopped"})


@app.route("/trade")
def trade():
    return render_template_string(TRADING_HTML)


@app.route("/api/manual/buy_pair", methods=["POST"])
def api_manual_buy_pair():
    data = request.json or {}
    pair = data.get("pair", "a")
    shares = int(data.get("shares", 6))
    if not state.markets:
        return jsonify({"ok": False, "msg": "No markets loaded"})
    key1, key2 = ("btc_up", "eth_down") if pair == "a" else ("btc_down", "eth_up")
    mkt1, mkt2 = state.markets.get(key1), state.markets.get(key2)
    price1, price2 = state.prices.get(key1), state.prices.get(key2)
    if not mkt1 or not mkt2 or price1 is None or price2 is None:
        return jsonify({"ok": False, "msg": "Markets or prices not ready"})
    from bot import _get_clob_client, TAKE_PROFIT, DRY_RUN
    from py_clob_client.clob_types import OrderArgs, OrderType
    from py_clob_client.order_builder.constants import BUY, SELL
    if DRY_RUN:
        state.add_trade_log(f"DRY MANUAL BUY PAIR-{pair.upper()} {shares}x each")
        return jsonify({"ok": True, "msg": "DRY RUN"})
    client = _get_clob_client()
    results = []
    for (mkt, price, key) in [(mkt1, price1, key1), (mkt2, price2, key2)]:
        try:
            order_args = OrderArgs(price=float(price), size=float(shares), side=BUY,
                                   token_id=str(mkt["token_id"]), fee_rate_bps=1000)
            result = client.create_and_post_order(order_args)
            order_id = (result or {}).get("orderID", "")
            with state._lock:
                state.total_bought += round(float(price) * shares, 4)
            state.add_trade_log(f"MANUAL BUY {shares}x {key} @ {price:.3f}")
            tp_args = OrderArgs(price=TAKE_PROFIT, size=float(shares), side=SELL,
                                token_id=str(mkt["token_id"]), fee_rate_bps=1000)
            signed = client.create_order(tp_args)
            client.post_order(signed, OrderType.GTC)
            state.add_trade_log(f"MANUAL TP {shares}x {key} @ {TAKE_PROFIT}")
            results.append({"key": key, "ok": True, "order_id": order_id[:12] if order_id else ""})
        except Exception as e:
            results.append({"key": key, "ok": False, "error": str(e)})
            log.warning("manual buy_pair %s error: %s", key, e)
    return jsonify({"ok": all(r["ok"] for r in results), "results": results})


@app.route("/api/manual/buy_token", methods=["POST"])
def api_manual_buy_token():
    data = request.json or {}
    key = data.get("key", "")
    shares = int(data.get("shares", 6))
    if key not in ("btc_up", "btc_down", "eth_up", "eth_down"):
        return jsonify({"ok": False, "msg": "Invalid token key"})
    mkt = state.markets.get(key)
    price = state.prices.get(key)
    if not mkt or price is None:
        return jsonify({"ok": False, "msg": "Market or price not ready"})
    from bot import _get_clob_client, TAKE_PROFIT, DRY_RUN
    from py_clob_client.clob_types import OrderArgs, OrderType
    from py_clob_client.order_builder.constants import BUY, SELL
    if DRY_RUN:
        state.add_trade_log(f"DRY MANUAL BUY {shares}x {key}")
        return jsonify({"ok": True, "msg": "DRY RUN"})
    try:
        client = _get_clob_client()
        order_args = OrderArgs(price=float(price), size=float(shares), side=BUY,
                               token_id=str(mkt["token_id"]), fee_rate_bps=1000)
        result = client.create_and_post_order(order_args)
        order_id = (result or {}).get("orderID", "")
        with state._lock:
            state.total_bought += round(float(price) * shares, 4)
        state.add_trade_log(f"MANUAL BUY {shares}x {key} @ {price:.3f}")
        tp_args = OrderArgs(price=TAKE_PROFIT, size=float(shares), side=SELL,
                            token_id=str(mkt["token_id"]), fee_rate_bps=1000)
        signed = client.create_order(tp_args)
        client.post_order(signed, OrderType.GTC)
        state.add_trade_log(f"MANUAL TP {shares}x {key} @ {TAKE_PROFIT}")
        return jsonify({"ok": True, "order_id": order_id[:12] if order_id else ""})
    except Exception as e:
        log.warning("manual buy_token %s error: %s", key, e)
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/manual/sell_token", methods=["POST"])
def api_manual_sell_token():
    data = request.json or {}
    key = data.get("key", "")
    shares = float(data.get("shares", 0))
    if key not in ("btc_up", "btc_down", "eth_up", "eth_down"):
        return jsonify({"ok": False, "msg": "Invalid token key"})
    mkt = state.markets.get(key)
    price = state.prices.get(key)
    if not mkt or price is None:
        return jsonify({"ok": False, "msg": "Market or price not ready"})
    if shares <= 0:
        shares = state.token_balances.get(key, 0)
    if shares <= 0:
        return jsonify({"ok": False, "msg": "No shares to sell"})
    from bot import _get_clob_client, DRY_RUN
    from py_clob_client.clob_types import OrderArgs, OrderType
    from py_clob_client.order_builder.constants import SELL
    if DRY_RUN:
        state.add_trade_log(f"DRY MANUAL SELL {shares}x {key}")
        return jsonify({"ok": True, "msg": "DRY RUN"})
    try:
        client = _get_clob_client()
        sell_price = max(0.01, float(price) - 0.01)
        order_args = OrderArgs(price=sell_price, size=float(shares), side=SELL,
                               token_id=str(mkt["token_id"]), fee_rate_bps=1000)
        signed = client.create_order(order_args)
        result = client.post_order(signed, OrderType.GTC)
        order_id = (result or {}).get("orderID", "")
        with state._lock:
            state.total_sold += round(sell_price * shares, 4)
        state.add_trade_log(f"MANUAL SELL {shares}x {key} @ {sell_price:.3f}")
        return jsonify({"ok": True, "order_id": order_id[:12] if order_id else ""})
    except Exception as e:
        log.warning("manual sell_token %s error: %s", key, e)
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "dry_run": os.getenv("DRY_RUN", "true")})


# ── Startup ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
