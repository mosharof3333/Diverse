"""
Polymarket 5-Min BTC/ETH Spread Bot
Strategy: Cross-market spread trading on 5-minute window markets
"""

import asyncio
import aiohttp
import time
import json
import os
import logging
from datetime import datetime, timezone
from typing import Optional
from state import BotState

# ── Config ────────────────────────────────────────────────────────────────────
# Three entry thresholds per direction per window
SPREAD_ENTRIES  = [0.10, 0.15, 0.30]
# Min price of the cheaper token per entry level (relaxed for first entry)
MIN_PRICES      = [0.20, 0.50, 0.50]
TAKE_PROFIT     = float(os.getenv("TAKE_PROFIT",     "0.985"))
SHARES          = int(os.getenv("SHARES",            "6"))
FORCE_CLOSE_SEC = float(os.getenv("FORCE_CLOSE_SEC", "30"))
POLL_MS         = int(os.getenv("POLL_MS",           "500"))
DRY_RUN         = os.getenv("DRY_RUN", "false").lower() == "true"

GAMMA_API      = "https://gamma-api.polymarket.com"
CLOB_API       = "https://clob.polymarket.com"
FUNDER_ADDRESS = "0x43f39b3abdc334623d822e8b25c00813638492fe"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("bot")

# ── CLOB client (lazy init, reused across orders) ─────────────────────────────
_clob_client = None

def _get_clob_client():
    global _clob_client
    if _clob_client is None:
        from py_clob_client.client import ClobClient
        from py_clob_client.constants import POLYGON
        pk = os.getenv("POLY_PRIVATE_KEY")
        if not pk:
            raise RuntimeError("POLY_PRIVATE_KEY env var is not set")
        # Level 1 — signing key + funder
        client = ClobClient(
            host=CLOB_API,
            chain_id=POLYGON,
            key=pk,
            funder=FUNDER_ADDRESS,
            signature_type=2,   # POLY_PROXY — MetaMask / proxy wallet
        )
        # Level 2 — derive API credentials from the private key
        creds = client.derive_api_key()
        client.set_api_creds(creds)
        _clob_client = client
        log.info(f"ClobClient ready (L2) | funder={FUNDER_ADDRESS[:10]}… sig_type=2")
    return _clob_client

# ── Market Discovery ──────────────────────────────────────────────────────────
async def find_5min_markets(session: aiohttp.ClientSession) -> Optional[dict]:
    """
    Find active BTC/ETH 5-min markets using deterministic slug lookup.

    Polymarket names these events: {asset}-updown-5m-{window_ts}
    where window_ts = current Unix timestamp rounded DOWN to the nearest 300s.
    The event contains ONE market whose clobTokenIds JSON string holds
    [up_token_id, down_token_id].

    API: GET /events/slug/{slug}  →  {"markets": [{"clobTokenIds": "[id0,id1]", ...}]}
    """
    now_ts    = int(time.time())
    window_ts = (now_ts // 300) * 300

    markets = {"btc_up": None, "btc_down": None, "eth_up": None, "eth_down": None}

    for asset in ("btc", "eth"):
        slug = f"{asset}-updown-5m-{window_ts}"
        url  = f"{GAMMA_API}/events/slug/{slug}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status != 200:
                    log.warning(f"Slug {slug} → HTTP {r.status}")
                    continue
                data = await r.json(content_type=None)

                mkt_list = data.get("markets", [])
                if not mkt_list:
                    log.warning(f"Slug {slug} → no markets in response")
                    continue

                mkt = mkt_list[0]
                raw = mkt.get("clobTokenIds", "[]")
                token_ids = json.loads(raw) if isinstance(raw, str) else raw

                if len(token_ids) < 2:
                    log.warning(f"Slug {slug} → expected 2 token IDs, got {token_ids}")
                    continue

                end_date = (mkt.get("endDate") or mkt.get("end_date_iso")
                            or data.get("endDate") or data.get("end_date_iso"))
                base = {
                    "market_id":   mkt.get("id"),
                    "conditionId": mkt.get("conditionId"),
                    "end_date":    end_date,
                }
                markets[f"{asset}_up"]   = {**base, "token_id": token_ids[0]}
                markets[f"{asset}_down"] = {**base, "token_id": token_ids[1]}
                log.info(f"  ✓ {asset} slug={slug} "
                         f"up={str(token_ids[0])[:16]}… down={str(token_ids[1])[:16]}…")

        except Exception as e:
            log.warning(f"Slug fetch failed for {slug}: {e}")

    found = sum(1 for v in markets.values() if v)
    log.info(f"Markets found: {found}/4")
    return markets if found == 4 else None


# ── Price Fetching ────────────────────────────────────────────────────────────
async def get_prices(session: aiohttp.ClientSession, markets: dict) -> Optional[dict]:
    """Get current BUY price for each token from the CLOB /price endpoint."""
    prices = {}
    for key, mkt in markets.items():
        if not mkt:
            return None
        try:
            token_id = mkt["token_id"]
            url = f"{CLOB_API}/price?token_id={token_id}&side=BUY"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as r:
                data = await r.json(content_type=None)
                price = data.get("price")
                prices[key] = float(price) if price is not None else None
        except Exception as e:
            log.warning(f"Price fetch failed for {key}: {e}")
            return None
    return prices


# ── Order Execution ───────────────────────────────────────────────────────────
async def place_order(session: aiohttp.ClientSession, market: dict, side: str, shares: int, state: BotState):
    """Place a BUY order. DRY_RUN=true just logs; otherwise signs + submits via ClobClient."""
    token_id = market["token_id"]
    price = state.prices.get(next(k for k, v in state.markets.items() if v == market))

    if DRY_RUN:
        log.info(f"  [DRY RUN] BUY {shares}x {side} @ {price:.3f} | token={str(token_id)[:16]}…")
        state.add_trade_log(f"DRY BUY {shares}x {side} @ {price:.3f}")
        return {"dry": True, "side": side, "shares": shares, "price": price}

    from py_clob_client.clob_types import OrderArgs, BalanceAllowanceParams, AssetType
    from py_clob_client.order_builder.constants import BUY

    client     = _get_clob_client()
    loop       = asyncio.get_event_loop()
    order_args = OrderArgs(
        price=float(price),
        size=float(shares),
        side=BUY,
        token_id=str(token_id),
        fee_rate_bps=1000,
    )

    # ── Step 1: place the order — abort if this fails ──────────────────────
    try:
        result   = await loop.run_in_executor(None, lambda: client.create_and_post_order(order_args))
        order_id = (result or {}).get("orderID", "")
    except Exception as e:
        log.error(f"BUY order failed: {e}")
        return None

    # Order placed — record immediately so traded flag is set regardless of step 2
    state.total_bought += round(price * float(shares), 4)
    log.info(f"BUY placed | {side} {shares}x @ {price:.3f} | {order_id[:12]}")
    state.add_trade_log(f"BUY {shares}x {side} @ {price:.3f} | {order_id[:12]}")

    # ── Step 2: read actual filled balance (best-effort, never aborts) ────
    filled = float(shares)
    try:
        await asyncio.sleep(0.5)
        bal_params = BalanceAllowanceParams(
            asset_type=AssetType.CONDITIONAL, token_id=str(token_id), signature_type=2
        )
        bal_resp = await loop.run_in_executor(
            None, lambda: client.get_balance_allowance(params=bal_params)
        )
        actual = float(bal_resp.get("balance", 0)) / 1e6
        if actual > 0:
            filled = actual
    except Exception as e:
        log.warning(f"Balance check after BUY failed (using {shares}): {e}")

    result = result or {}
    result["filled_shares"] = filled
    return result


async def place_take_profit(market: dict, side: str, shares: float, state: BotState):
    """Place a GTC sell at TAKE_PROFIT price immediately after a buy."""
    token_id = market["token_id"]

    if DRY_RUN:
        log.info(f"  [DRY RUN] TP SELL {shares}x {side} @ {TAKE_PROFIT}")
        state.add_trade_log(f"DRY TP {shares}x {side} @ {TAKE_PROFIT}")
        return

    try:
        from py_clob_client.clob_types import OrderArgs, OrderType
        from py_clob_client.order_builder.constants import SELL

        client = _get_clob_client()
        loop   = asyncio.get_event_loop()
        order_args = OrderArgs(
            price=TAKE_PROFIT,
            size=float(shares),
            side=SELL,
            token_id=str(token_id),
            fee_rate_bps=1000,
        )
        signed = await loop.run_in_executor(None, lambda: client.create_order(order_args))
        result = await loop.run_in_executor(None, lambda: client.post_order(signed, OrderType.GTC))
        order_id = (result or {}).get("orderID", "")
        log.info(f"TP order placed | {side} {shares:.4f}x @ {TAKE_PROFIT} | {order_id[:12]}")
        state.add_trade_log(f"TP {shares:.4f}x {side} @ {TAKE_PROFIT} | {order_id[:12]}")
    except Exception as e:
        log.error(f"TP order failed: {e}")


async def sell_position(session: aiohttp.ClientSession, position: dict, state: BotState, reason: str,
                        force: bool = False):
    """
    Close a position.
    force=True  → FAK order at aggressive price (0.01) — guarantees fill before window end.
    force=False → GTC limit order at current market price (normal exit).
    """
    mkt           = position["market"]
    shares        = position["shares"]
    side          = position["side"]
    token_id      = mkt["token_id"]
    current_price = state.prices.get(position["price_key"])
    pnl = (current_price - position["entry_price"]) * shares if current_price else 0

    if DRY_RUN:
        tag = "FORCE" if force else "DRY"
        log.info(f"  [{tag} RUN] SELL {shares}x {side} @ {current_price:.3f} | PnL: {pnl:+.3f} | {reason}")
        state.add_trade_log(f"DRY SELL {shares}x {side} @ {current_price:.3f} PnL={pnl:+.3f} [{reason}]")
        state.total_pnl += pnl
        if pnl > 0:
            state.wins += 1
        else:
            state.losses += 1
        return True

    try:
        from py_clob_client.clob_types import OrderArgs, OrderType
        from py_clob_client.order_builder.constants import SELL

        client = _get_clob_client()
        loop   = asyncio.get_event_loop()

        if force:
            # FAK at 0.01 — fills immediately against best available bid,
            # cancels any remainder. Guarantees no tokens are held past window end.
            sell_price = 0.01
            order_type = OrderType.FAK
            log.warning(f"FORCE SELL (FAK) | {side} {shares:.4f}x @ {sell_price} | {reason}")
        else:
            sell_price = float(current_price)
            order_type = OrderType.GTC

        order_args = OrderArgs(
            price=sell_price,
            size=float(shares),
            side=SELL,
            token_id=str(token_id),
            fee_rate_bps=1000,
        )
        signed = await loop.run_in_executor(None, lambda: client.create_order(order_args))
        result = await loop.run_in_executor(None, lambda: client.post_order(signed, order_type))

        order_id = (result or {}).get("orderID", "")
        state.total_sold += round(sell_price * float(shares), 4)
        log.info(f"SELL placed | {side} {shares:.4f}x @ {sell_price:.3f} PnL={pnl:+.3f} [{reason}] | {order_id[:12]}")
        state.add_trade_log(f"SELL {shares:.4f}x {side} @ {sell_price:.3f} PnL={pnl:+.3f} [{reason}]")
        state.total_pnl += pnl
        if pnl > 0:
            state.wins += 1
        else:
            state.losses += 1
        return True
    except Exception as e:
        log.error(f"SELL order failed: {e}")
        return False


# ── Core Strategy ─────────────────────────────────────────────────────────────
async def evaluate_strategy(session: aiohttp.ClientSession, direction: str, state: BotState, traded: dict):
    """
    direction: 'up' or 'down'
    Up to 3 entries per window at spread thresholds 0.10 / 0.15 / 0.30.
    Each entry immediately places a GTC take-profit sell at TAKE_PROFIT (0.985).
    Exit is handled by the TP order filling or force-close at T-30s — no
    spread-compression exit logic.
    """
    btc_key = f"btc_{direction}"
    eth_key = f"eth_{direction}"

    btc_price = state.prices.get(btc_key)
    eth_price  = state.prices.get(eth_key)

    if btc_price is None or eth_price is None:
        return

    spread = abs(btc_price - eth_price)
    state.spreads[direction] = spread

    trade_count = traded[direction]
    if trade_count >= len(SPREAD_ENTRIES):
        return   # max 3 trades per direction per window

    threshold = SPREAD_ENTRIES[trade_count]
    min_price = MIN_PRICES[trade_count]

    if spread < threshold:
        return

    cheaper_side  = "btc" if btc_price < eth_price else "eth"
    cheaper_price = btc_price if cheaper_side == "btc" else eth_price
    dearer_price  = eth_price if cheaper_side == "btc" else btc_price
    cheaper_key   = f"{cheaper_side}_{direction}"
    cheaper_mkt   = state.markets.get(cheaper_key)

    if cheaper_price <= min_price or dearer_price <= 0.20:
        return

    log.info(
        f"[{direction.upper()}] ENTRY #{trade_count + 1} | "
        f"spread={spread:.3f} >= {threshold:.2f} | buy {cheaper_key} @ {cheaper_price:.3f}"
    )
    result = await place_order(session, cheaper_mkt, cheaper_key, SHARES, state)

    if result:
        filled = result.get("filled_shares", float(SHARES))

        # Place take-profit GTC sell at 0.985 immediately
        await place_take_profit(cheaper_mkt, cheaper_key, filled, state)

        pos = state.positions.get(direction)
        if pos is None:
            state.positions[direction] = {
                "side":         cheaper_side,
                "price_key":    cheaper_key,
                "market":       cheaper_mkt,
                "shares":       filled,
                "entry_price":  cheaper_price,
                "entry_spread": spread,
                "entry_time":   time.time(),
            }
        else:
            # Accumulate into existing position — weighted average entry price
            total = pos["shares"] + filled
            pos["entry_price"] = (pos["entry_price"] * pos["shares"] + cheaper_price * filled) / total
            pos["shares"]      = total

        traded[direction] += 1
        state.total_trades += 1


# ── Account Sync ─────────────────────────────────────────────────────────────
async def sync_account_state(state: BotState):
    """Fetch real USDC balance + actual token holdings from CLOB and update state."""
    if DRY_RUN:
        return
    try:
        from py_clob_client.clob_types import BalanceAllowanceParams, AssetType
        client = _get_clob_client()
        loop   = asyncio.get_event_loop()

        # Real USDC balance in the proxy wallet
        usdc_params = BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
        usdc_resp   = await loop.run_in_executor(None, lambda: client.get_balance_allowance(params=usdc_params))
        state.usdc_balance = round(float(usdc_resp.get("balance", 0)) / 1e6, 4)

        # Real token balance for each open position
        for pos in state.positions.values():
            if not pos:
                continue
            token_id  = pos["market"]["token_id"]
            tok_params = BalanceAllowanceParams(
                asset_type=AssetType.CONDITIONAL,
                token_id=str(token_id),
                signature_type=2,
            )
            tok_resp  = await loop.run_in_executor(
                None, lambda p=tok_params: client.get_balance_allowance(params=p)
            )
            real = round(float(tok_resp.get("balance", 0)) / 1e6, 6)
            pos["real_shares"] = real          # live chain value shown in dashboard

    except Exception as e:
        log.warning(f"Account sync failed: {e}")


# ── Force Close ───────────────────────────────────────────────────────────────
async def force_close_all(session: aiohttp.ClientSession, state: BotState):
    log.warning(f"⚡ FORCE CLOSE — FAK sell all positions at {FORCE_CLOSE_SEC}s before window end")
    state.force_closing = True

    # Sync real balances first — take-profit GTC may have already filled
    await sync_account_state(state)

    for direction in ["up", "down"]:
        pos = state.positions.get(direction)
        if not pos:
            continue
        real = pos.get("real_shares", pos["shares"])
        if real <= 0.001:
            log.info(f"[{direction.upper()}] TP already filled — skipping force close")
            state.positions[direction] = None
            continue
        # Use actual chain balance for the FAK sell
        pos_to_close = dict(pos)
        pos_to_close["shares"] = real
        await sell_position(session, pos_to_close, state, f"FORCE_CLOSE_{FORCE_CLOSE_SEC}s", force=True)
        state.positions[direction] = None

    state.force_closing = False
    log.info("✓ All positions closed")


# ── Main Loop ─────────────────────────────────────────────────────────────────
async def run_bot(state: BotState):
    log.info(f"Bot starting | DRY_RUN={DRY_RUN} | ENTRIES={SPREAD_ENTRIES} | TP={TAKE_PROFIT} | SHARES={SHARES}")

    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:

        while state.running:
            # ── Discover markets ──────────────────────────────────────────
            log.info("Discovering 5-min markets…")
            markets = None
            while state.running and not markets:
                markets = await find_5min_markets(session)
                if not markets:
                    log.warning("Markets not found — retrying in 10s")
                    await asyncio.sleep(10)

            if not state.running:
                break

            state.markets = markets
            window_end_str = (
                markets["btc_up"].get("end_date") or
                markets["eth_up"].get("end_date")
            )

            window_end_ts = None
            if window_end_str:
                try:
                    from dateutil import parser as dp
                    window_end_ts = dp.parse(window_end_str).timestamp()
                except Exception:
                    pass

            state.window_end = window_end_ts
            log.info(f"Window ends: {window_end_str}")

            # ── Poll loop for this window ─────────────────────────────────
            force_closed = False
            traded       = {"up": 0, "down": 0}  # counts entries per direction (max 3)
            tick         = 0
            while state.running:
                now = time.time()

                # Check if we need to force close
                if window_end_ts and not force_closed:
                    remaining = window_end_ts - now
                    state.seconds_remaining = remaining
                    if remaining <= FORCE_CLOSE_SEC:
                        await force_close_all(session, state)
                        force_closed = True
                        # Wait for new window
                        log.info("Waiting 8s for new window…")
                        await asyncio.sleep(8)
                        break

                # Fetch prices
                prices = await get_prices(session, markets)
                if prices:
                    state.prices = prices
                    state.last_update = time.time()
                    await evaluate_strategy(session, "up",   state, traded)
                    await evaluate_strategy(session, "down", state, traded)
                    state.record_prices()

                # Sync real account balances every 10 ticks (~5s)
                tick += 1
                if tick % 10 == 0:
                    await sync_account_state(state)

                await asyncio.sleep(POLL_MS / 1000)


def start_bot(state: BotState):
    """Entry point called from server.py."""
    asyncio.run(run_bot(state))
