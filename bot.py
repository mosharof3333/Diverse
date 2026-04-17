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
MIN_PRICES      = [0.20, 0.20, 0.20]
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
async def evaluate_pair(session: aiohttp.ClientSession, pair: str, state: BotState, traded: dict):
    """
    pair 'a': BTC_UP + ETH_DOWN — spread = abs(btc_up_price - eth_down_price)
    pair 'b': BTC_DOWN + ETH_UP — spread = abs(btc_down_price - eth_up_price)

    When spread >= threshold, buy BOTH tokens in the pair and immediately
    place a GTC TP sell at 0.985 for each. Up to 3 entries per pair per window.
    """
    if pair == "a":
        key1, key2 = "btc_up", "eth_down"
    else:
        key1, key2 = "btc_down", "eth_up"

    price1 = state.prices.get(key1)
    price2 = state.prices.get(key2)

    if price1 is None or price2 is None:
        return

    spread = abs(price1 - price2)
    state.spreads[pair] = spread

    trade_count = traded[pair]
    if trade_count >= len(SPREAD_ENTRIES):
        return

    threshold = SPREAD_ENTRIES[trade_count]
    if spread < threshold:
        return

    if price1 <= 0.20 or price2 <= 0.20:
        return

    mkt1 = state.markets.get(key1)
    mkt2 = state.markets.get(key2)

    log.info(
        f"[PAIR-{pair.upper()}] ENTRY #{trade_count + 1} | "
        f"spread={spread:.3f} >= {threshold:.2f} | "
        f"{key1} @ {price1:.3f} + {key2} @ {price2:.3f}"
    )

    result1 = await place_order(session, mkt1, key1, SHARES, state)
    result2 = await place_order(session, mkt2, key2, SHARES, state)

    # ── Partial failure: retry the failed side once, then cancel if still failing ──
    if bool(result1) != bool(result2):
        failed_key  = key2  if result1 else key1
        failed_mkt  = mkt2  if result1 else mkt1
        ok_result   = result1 if result1 else result2
        ok_key      = key1  if result1 else key2
        ok_mkt      = mkt1  if result1 else mkt2
        ok_price    = price1 if result1 else price2

        log.warning(f"[PAIR-{pair.upper()}] {failed_key} buy failed — retrying in 1s")
        await asyncio.sleep(1)
        retry = await place_order(session, failed_mkt, failed_key, SHARES, state)

        if retry:
            # Retry succeeded — treat as normal both-sides fill
            result1 = ok_result if ok_key == key1 else retry
            result2 = retry     if ok_key == key1 else ok_result
        else:
            # Retry also failed — sell the successful side and stay flat
            log.warning(
                f"[PAIR-{pair.upper()}] retry also failed — selling {ok_key} to stay flat"
            )
            ok_filled = ok_result.get("filled_shares", float(SHARES))
            cancel_pos = {
                "market":      ok_mkt,
                "side":        ok_key,
                "price_key":   ok_key,
                "shares":      ok_filled,
                "entry_price": ok_price,
            }
            await sell_position(session, cancel_pos, state, "PAIR_CANCEL", force=False)
            state.add_trade_log(f"PAIR CANCEL — sold {ok_key} x{ok_filled:.4f} (other side failed)")
            return  # abort — traded[pair] NOT incremented, threshold can trigger again

    filled1 = result1.get("filled_shares", float(SHARES)) if result1 else 0.0
    filled2 = result2.get("filled_shares", float(SHARES)) if result2 else 0.0

    if result1:
        await place_take_profit(mkt1, key1, filled1, state)
    if result2:
        await place_take_profit(mkt2, key2, filled2, state)

    if result1 or result2:
        pos = state.positions.get(pair)
        if pos is None:
            state.positions[pair] = {
                "tokens": [
                    {"key": key1, "market": mkt1, "shares": filled1, "entry_price": price1},
                    {"key": key2, "market": mkt2, "shares": filled2, "entry_price": price2},
                ],
                "entry_spread": spread,
                "entry_time":   time.time(),
            }
        else:
            pos["tokens"][0]["shares"] += filled1
            pos["tokens"][1]["shares"] += filled2

        traded[pair] += 1
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

        usdc_params = BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
        usdc_resp   = await loop.run_in_executor(None, lambda: client.get_balance_allowance(params=usdc_params))
        state.usdc_balance = round(float(usdc_resp.get("balance", 0)) / 1e6, 4)

        for pos in state.positions.values():
            if not pos:
                continue
            for token in pos["tokens"]:
                token_id   = token["market"]["token_id"]
                tok_params = BalanceAllowanceParams(
                    asset_type=AssetType.CONDITIONAL,
                    token_id=str(token_id),
                    signature_type=2,
                )
                tok_resp = await loop.run_in_executor(
                    None, lambda p=tok_params: client.get_balance_allowance(params=p)
                )
                token["real_shares"] = round(float(tok_resp.get("balance", 0)) / 1e6, 6)

    except Exception as e:
        log.warning(f"Account sync failed: {e}")


# ── Force Close ───────────────────────────────────────────────────────────────
async def force_close_all(session: aiohttp.ClientSession, state: BotState):
    log.warning(f"⚡ FORCE CLOSE — FAK sell all positions at {FORCE_CLOSE_SEC}s before window end")
    state.force_closing = True

    await sync_account_state(state)

    for pair in ["a", "b"]:
        pos = state.positions.get(pair)
        if not pos:
            continue
        for token in pos["tokens"]:
            real = token.get("real_shares", token["shares"])
            if real <= 0.001:
                log.info(f"TP already filled for {token['key']} — skipping")
                continue
            single = {
                "market":      token["market"],
                "side":        token["key"],
                "price_key":   token["key"],
                "shares":      real,
                "entry_price": token["entry_price"],
            }
            await sell_position(session, single, state, f"FORCE_CLOSE_{FORCE_CLOSE_SEC}s", force=True)
        state.positions[pair] = None

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
            traded       = {"a": 0, "b": 0}  # counts entries per pair (max 3)
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
                    await evaluate_pair(session, "a", state, traded)
                    await evaluate_pair(session, "b", state, traded)
                    state.record_prices()

                # Sync real account balances every 10 ticks (~5s)
                tick += 1
                if tick % 10 == 0:
                    await sync_account_state(state)

                await asyncio.sleep(POLL_MS / 1000)


def start_bot(state: BotState):
    """Entry point called from server.py."""
    asyncio.run(run_bot(state))
