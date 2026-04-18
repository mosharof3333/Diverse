"""
Flask server: serves dashboard UI + REST API + starts bot in background thread.
"""

import os
import json
import time
import threading
import logging
import requests as _req
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, jsonify, request, render_template_string
from state import BotState
from bot import start_bot
from dashboard import DASHBOARD_HTML, TRADING_HTML

log = logging.getLogger("server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)
state = BotState()
bot_thread = None

GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API  = "https://clob.polymarket.com"

# Cache markets per 5-min window so we don't hammer Gamma API on every poll
_trade_markets     = {}
_trade_window_ts   = 0
_trade_markets_lock = threading.Lock()

# ── Auto-start ────────────────────────────────────────────────────────────────
_auto_start = os.getenv("AUTO_START", "true").lower() == "true"
if _auto_start:
    log.info("AUTO_START=true — starting bot automatically")
    state.running = True
    bot_thread = threading.Thread(target=start_bot, args=(state,), daemon=True)
    bot_thread.start()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _discover_markets_sync():
    """Fetch current 5-min BTC/ETH markets from Gamma API synchronously."""
    now_ts    = int(time.time())
    window_ts = (now_ts // 300) * 300
    markets   = {}
    for asset in ("btc", "eth"):
        slug = f"{asset}-updown-5m-{window_ts}"
        try:
            r = _req.get(f"{GAMMA_API}/events/slug/{slug}", timeout=5)
            if r.status_code != 200:
                continue
            data     = r.json()
            mkt_list = data.get("markets", [])
            if not mkt_list:
                continue
            mkt      = mkt_list[0]
            raw      = mkt.get("clobTokenIds", "[]")
            ids      = json.loads(raw) if isinstance(raw, str) else raw
            if len(ids) < 2:
                continue
            end_date = (mkt.get("endDate") or mkt.get("end_date_iso")
                        or data.get("endDate") or data.get("end_date_iso"))
            base = {"market_id": mkt.get("id"), "conditionId": mkt.get("conditionId"),
                    "end_date": end_date}
            markets[f"{asset}_up"]   = {**base, "token_id": ids[0]}
            markets[f"{asset}_down"] = {**base, "token_id": ids[1]}
        except Exception as e:
            log.warning("trade market discovery %s: %s", slug, e)
    return markets if len(markets) == 4 else {}


def _get_trade_markets():
    """Return cached markets, refreshing when the 5-min window changes."""
    global _trade_markets, _trade_window_ts
    now_ts    = int(time.time())
    window_ts = (now_ts // 300) * 300
    with _trade_markets_lock:
        if _trade_window_ts != window_ts or not _trade_markets:
            # Use bot's already-discovered markets if available and fresh
            if len(state.markets) == 4:
                _trade_markets   = dict(state.markets)
                _trade_window_ts = window_ts
            else:
                discovered = _discover_markets_sync()
                if discovered:
                    _trade_markets   = discovered
                    _trade_window_ts = window_ts
                    state.markets    = discovered   # share with bot
        return dict(_trade_markets)


def _fetch_price(key, token_id):
    try:
        r = _req.get(f"{CLOB_API}/price?token_id={token_id}&side=BUY", timeout=3)
        p = r.json().get("price") if r.status_code == 200 else None
        return key, float(p) if p is not None else None
    except Exception:
        return key, None


def _fetch_prices_sync(markets):
    """Fetch all 4 token prices in parallel."""
    prices = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_price, k, m["token_id"]): k for k, m in markets.items()}
        for f in as_completed(futs):
            k, p = f.result()
            prices[k] = p
    return prices


# ── Standard API Routes ───────────────────────────────────────────────────────

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


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "dry_run": os.getenv("DRY_RUN", "true")})


# ── Manual Trading Routes ─────────────────────────────────────────────────────

@app.route("/trade")
def trade():
    return render_template_string(TRADING_HTML)


@app.route("/api/trade/data")
def api_trade_data():
    """Live price feed for the manual trading dashboard — works independently of the bot."""
    markets = _get_trade_markets()
    if not markets:
        return jsonify({"ok": False, "msg": "Markets not available yet — retry in a moment"})

    prices = _fetch_prices_sync(markets)

    # Update shared state so bot also benefits
    state.prices     = {k: v for k, v in prices.items() if v is not None}
    state.last_update = time.time()

    pa1, pa2 = prices.get("btc_up"), prices.get("eth_down")
    pb1, pb2 = prices.get("btc_down"), prices.get("eth_up")
    spread_a = round(abs(pa1 - pa2), 4) if pa1 and pa2 else None
    spread_b = round(abs(pb1 - pb2), 4) if pb1 and pb2 else None

    # Window time remaining
    end_ts = None
    for m in markets.values():
        if m.get("end_date"):
            try:
                from dateutil import parser as dp
                end_ts = dp.parse(m["end_date"]).timestamp()
                break
            except Exception:
                pass
    remaining = round(end_ts - time.time(), 1) if end_ts else None

    return jsonify({
        "ok":       True,
        "prices":   prices,
        "spreads":  {"a": spread_a, "b": spread_b},
        "markets_ready": len(markets) == 4,
        "seconds_remaining": remaining,
        "usdc_balance":   state.usdc_balance,
        "token_balances": {k: round(v, 6) for k, v in state.token_balances.items()},
        "stats": {
            "total_pnl":    round(state.total_pnl,    4),
            "total_trades": state.total_trades,
            "wins":         state.wins,
            "losses":       state.losses,
            "total_bought": round(state.total_bought, 4),
            "total_sold":   round(state.total_sold,   4),
        },
        "bot_running": state.running,
        "trade_log":   list(state.trade_log)[:25],
    })


@app.route("/api/manual/buy_pair", methods=["POST"])
def api_manual_buy_pair():
    data   = request.json or {}
    pair   = data.get("pair", "a")
    shares = int(data.get("shares", 6))

    markets = _get_trade_markets()
    if not markets:
        return jsonify({"ok": False, "msg": "Markets not found — try again in a moment"})

    key1, key2 = ("btc_up", "eth_down") if pair == "a" else ("btc_down", "eth_up")
    mkt1, mkt2 = markets.get(key1), markets.get(key2)
    if not mkt1 or not mkt2:
        return jsonify({"ok": False, "msg": f"Markets for pair {pair} not loaded"})

    # Fresh prices
    prices = _fetch_prices_sync({key1: mkt1, key2: mkt2})
    price1, price2 = prices.get(key1), prices.get(key2)
    if price1 is None or price2 is None:
        return jsonify({"ok": False, "msg": "Could not fetch live prices"})

    from bot import _get_clob_client, TAKE_PROFIT, DRY_RUN
    from py_clob_client.clob_types import OrderArgs, OrderType
    from py_clob_client.order_builder.constants import BUY, SELL

    if DRY_RUN:
        state.add_trade_log(f"DRY MANUAL BUY PAIR-{pair.upper()} {shares}x @ {price1:.3f}+{price2:.3f}")
        return jsonify({"ok": True, "msg": f"DRY RUN — would buy {shares}x each at {price1:.3f} + {price2:.3f}"})

    client  = _get_clob_client()
    results = []
    for mkt, price, key in [(mkt1, price1, key1), (mkt2, price2, key2)]:
        try:
            buy_args = OrderArgs(price=float(price), size=float(shares), side=BUY,
                                 token_id=str(mkt["token_id"]), fee_rate_bps=1000)
            res      = client.create_and_post_order(buy_args)
            oid      = (res or {}).get("orderID", "")
            with state._lock:
                state.total_bought += round(float(price) * shares, 4)
            state.add_trade_log(f"MANUAL BUY {shares}x {key} @ {price:.3f} | {oid[:8]}")

            tp_args = OrderArgs(price=TAKE_PROFIT, size=float(shares), side=SELL,
                                token_id=str(mkt["token_id"]), fee_rate_bps=1000)
            signed  = client.create_order(tp_args)
            client.post_order(signed, OrderType.GTC)
            state.add_trade_log(f"MANUAL TP {shares}x {key} @ {TAKE_PROFIT}")
            results.append({"key": key, "ok": True, "price": price, "order_id": oid[:12]})
        except Exception as e:
            log.warning("manual buy_pair %s: %s", key, e)
            results.append({"key": key, "ok": False, "error": str(e)})

    return jsonify({"ok": all(r["ok"] for r in results), "results": results})


@app.route("/api/manual/buy_token", methods=["POST"])
def api_manual_buy_token():
    data   = request.json or {}
    key    = data.get("key", "")
    shares = int(data.get("shares", 6))

    if key not in ("btc_up", "btc_down", "eth_up", "eth_down"):
        return jsonify({"ok": False, "msg": "Invalid token key"})

    markets = _get_trade_markets()
    mkt     = markets.get(key)
    if not mkt:
        return jsonify({"ok": False, "msg": "Market not found — try again"})

    _, price = _fetch_price(key, mkt["token_id"])
    if price is None:
        return jsonify({"ok": False, "msg": "Could not fetch live price"})

    from bot import _get_clob_client, TAKE_PROFIT, DRY_RUN
    from py_clob_client.clob_types import OrderArgs, OrderType
    from py_clob_client.order_builder.constants import BUY, SELL

    if DRY_RUN:
        state.add_trade_log(f"DRY MANUAL BUY {shares}x {key} @ {price:.3f}")
        return jsonify({"ok": True, "msg": f"DRY RUN — would buy {shares}x {key} @ {price:.3f}"})

    try:
        client   = _get_clob_client()
        buy_args = OrderArgs(price=float(price), size=float(shares), side=BUY,
                             token_id=str(mkt["token_id"]), fee_rate_bps=1000)
        res      = client.create_and_post_order(buy_args)
        oid      = (res or {}).get("orderID", "")
        with state._lock:
            state.total_bought += round(float(price) * shares, 4)
        state.add_trade_log(f"MANUAL BUY {shares}x {key} @ {price:.3f} | {oid[:8]}")

        tp_args = OrderArgs(price=TAKE_PROFIT, size=float(shares), side=SELL,
                            token_id=str(mkt["token_id"]), fee_rate_bps=1000)
        signed  = client.create_order(tp_args)
        client.post_order(signed, OrderType.GTC)
        state.add_trade_log(f"MANUAL TP {shares}x {key} @ {TAKE_PROFIT}")
        return jsonify({"ok": True, "price": price, "order_id": oid[:12]})
    except Exception as e:
        log.warning("manual buy_token %s: %s", key, e)
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/manual/sell_token", methods=["POST"])
def api_manual_sell_token():
    data   = request.json or {}
    key    = data.get("key", "")
    shares = float(data.get("shares", 0))

    if key not in ("btc_up", "btc_down", "eth_up", "eth_down"):
        return jsonify({"ok": False, "msg": "Invalid token key"})

    markets = _get_trade_markets()
    mkt     = markets.get(key)
    if not mkt:
        return jsonify({"ok": False, "msg": "Market not found — try again"})

    _, price = _fetch_price(key, mkt["token_id"])
    if price is None:
        return jsonify({"ok": False, "msg": "Could not fetch live price"})

    if shares <= 0:
        shares = state.token_balances.get(key, 0)
    if shares <= 0:
        return jsonify({"ok": False, "msg": "No balance to sell"})

    from bot import _get_clob_client, DRY_RUN
    from py_clob_client.clob_types import OrderArgs, OrderType
    from py_clob_client.order_builder.constants import SELL

    if DRY_RUN:
        state.add_trade_log(f"DRY MANUAL SELL {shares:.4f}x {key}")
        return jsonify({"ok": True, "msg": f"DRY RUN — would sell {shares:.4f}x {key}"})

    try:
        client     = _get_clob_client()
        sell_price = max(0.01, round(float(price) - 0.01, 4))
        sell_args  = OrderArgs(price=sell_price, size=float(shares), side=SELL,
                               token_id=str(mkt["token_id"]), fee_rate_bps=1000)
        signed     = client.create_order(sell_args)
        res        = client.post_order(signed, OrderType.GTC)
        oid        = (res or {}).get("orderID", "")
        with state._lock:
            state.total_sold += round(sell_price * shares, 4)
        state.add_trade_log(f"MANUAL SELL {shares:.4f}x {key} @ {sell_price:.3f} | {oid[:8]}")
        return jsonify({"ok": True, "price": sell_price, "shares": shares, "order_id": oid[:12]})
    except Exception as e:
        log.warning("manual sell_token %s: %s", key, e)
        return jsonify({"ok": False, "error": str(e)})


# ── Startup ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
