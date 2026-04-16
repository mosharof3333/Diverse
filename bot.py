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
SPREAD_ENTRY    = float(os.getenv("SPREAD_ENTRY",    "0.15"))
SPREAD_EXIT     = float(os.getenv("SPREAD_EXIT",     "0.15"))
MIN_PRICE       = float(os.getenv("MIN_PRICE",       "0.50"))
SHARES          = int(os.getenv("SHARES",            "6"))
FORCE_CLOSE_SEC = float(os.getenv("FORCE_CLOSE_SEC", "4.9"))
POLL_MS         = int(os.getenv("POLL_MS",           "500"))
DRY_RUN         = os.getenv("DRY_RUN", "true").lower() == "true"

GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API  = "https://clob.polymarket.com"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("bot")

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
    """Place buy order. DRY_RUN=true just logs it."""
    token_id = market["token_id"]
    price = state.prices.get(next(k for k, v in state.markets.items() if v == market))

    if DRY_RUN:
        log.info(f"  [DRY RUN] BUY {shares} shares of {side} @ {price:.3f} | token={str(token_id)[:16]}…")
        state.add_trade_log(f"DRY BUY {shares}x {side} @ {price:.3f}")
        return {"dry": True, "side": side, "shares": shares, "price": price}

    # Real order via Polymarket CLOB API
    # Requires API key + signing — set POLY_API_KEY and POLY_PRIVATE_KEY in env
    api_key = os.getenv("POLY_API_KEY")
    if not api_key:
        log.error("POLY_API_KEY not set — cannot place real order")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "tokenID": token_id,
        "price": price,
        "side": "BUY",
        "size": shares,
        "orderType": "GTC",
    }
    try:
        async with session.post(f"{CLOB_API}/order", json=payload, headers=headers,
                                timeout=aiohttp.ClientTimeout(total=5)) as r:
            result = await r.json(content_type=None)
            log.info(f"Order placed: {result}")
            state.add_trade_log(f"BUY {shares}x {side} @ {price:.3f} | {result.get('orderID','')[:12]}")
            return result
    except Exception as e:
        log.error(f"Order failed: {e}")
        return None


async def sell_position(session: aiohttp.ClientSession, position: dict, state: BotState, reason: str):
    """Close/sell a position."""
    mkt = position["market"]
    shares = position["shares"]
    side = position["side"]
    token_id = mkt["token_id"]
    current_price = state.prices.get(position["price_key"])
    pnl = (current_price - position["entry_price"]) * shares if current_price else 0

    if DRY_RUN:
        log.info(f"  [DRY RUN] SELL {shares}x {side} @ {current_price:.3f} | PnL: {pnl:+.3f} | reason={reason}")
        state.add_trade_log(f"DRY SELL {shares}x {side} @ {current_price:.3f} PnL={pnl:+.3f} [{reason}]")
        state.total_pnl += pnl
        if pnl > 0:
            state.wins += 1
        else:
            state.losses += 1
        return True

    api_key = os.getenv("POLY_API_KEY")
    if not api_key:
        log.error("POLY_API_KEY not set")
        return False

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"tokenID": token_id, "price": current_price, "side": "SELL", "size": shares, "orderType": "GTC"}
    try:
        async with session.post(f"{CLOB_API}/order", json=payload, headers=headers,
                                timeout=aiohttp.ClientTimeout(total=5)) as r:
            result = await r.json(content_type=None)
            log.info(f"Sell placed: {result}")
            state.add_trade_log(f"SELL {shares}x {side} @ {current_price:.3f} PnL={pnl:+.3f} [{reason}]")
            state.total_pnl += pnl
            if pnl > 0:
                state.wins += 1
            else:
                state.losses += 1
            return True
    except Exception as e:
        log.error(f"Sell failed: {e}")
        return False


# ── Core Strategy ─────────────────────────────────────────────────────────────
async def evaluate_strategy(session: aiohttp.ClientSession, direction: str, state: BotState):
    """
    direction: 'up' or 'down'
    Compares btc_{direction} vs eth_{direction} prices.
    """
    btc_key = f"btc_{direction}"
    eth_key = f"eth_{direction}"

    btc_price = state.prices.get(btc_key)
    eth_price  = state.prices.get(eth_key)

    if btc_price is None or eth_price is None:
        return

    spread = abs(btc_price - eth_price)
    pos = state.positions.get(direction)

    state.spreads[direction] = spread

    # ── EXIT logic (position open) ─────────────────────────────────────────
    if pos:
        entry_spread   = pos["entry_spread"]
        entry_cheaper  = pos["side"]  # 'btc' or 'eth'
        current_cheaper = "btc" if btc_price < eth_price else "eth"
        current_price_of_pos = state.prices.get(pos["price_key"])
        pnl = (current_price_of_pos - pos["entry_price"]) * SHARES if current_price_of_pos else 0

        # Spread compressed or reversed by EXIT threshold
        spread_moved = (entry_spread - spread) >= SPREAD_EXIT

        if spread_moved:
            if pnl > 0:
                # Profitable — sell
                log.info(f"[{direction.upper()}] EXIT profitable | spread {spread:.3f} | PnL {pnl:+.4f}")
                sold = await sell_position(session, pos, state, "SPREAD_CLOSED_PROFIT")
                if sold:
                    state.positions[direction] = None
            else:
                # Not profitable — buy opposite side to rebalance
                opposite_key = eth_key if entry_cheaper == "btc" else btc_key
                opposite_mkt = state.markets.get(opposite_key)
                log.info(f"[{direction.upper()}] REBALANCE | spread {spread:.3f} | PnL {pnl:+.4f}")
                await place_order(session, opposite_mkt, opposite_key, SHARES, state)
                state.add_trade_log(f"REBALANCE {opposite_key} x{SHARES}")
        return

    # ── ENTRY logic (no position) ──────────────────────────────────────────
    if spread >= SPREAD_ENTRY and btc_price > MIN_PRICE and eth_price > MIN_PRICE:
        cheaper_side = "btc" if btc_price < eth_price else "eth"
        cheaper_key  = f"{cheaper_side}_{direction}"
        cheaper_mkt  = state.markets.get(cheaper_key)
        cheaper_price = btc_price if cheaper_side == "btc" else eth_price

        log.info(f"[{direction.upper()}] ENTRY | spread={spread:.3f} | buy {cheaper_key} @ {cheaper_price:.3f}")
        result = await place_order(session, cheaper_mkt, cheaper_key, SHARES, state)

        if result:
            state.positions[direction] = {
                "side":        cheaper_side,
                "price_key":   cheaper_key,
                "market":      cheaper_mkt,
                "shares":      SHARES,
                "entry_price": cheaper_price,
                "entry_spread": spread,
                "entry_time":  time.time(),
            }
            state.total_trades += 1


# ── Force Close ───────────────────────────────────────────────────────────────
async def force_close_all(session: aiohttp.ClientSession, state: BotState):
    log.warning("⚡ FORCE CLOSE — closing all positions at 4.9s before window end")
    state.force_closing = True
    for direction in ["up", "down"]:
        pos = state.positions.get(direction)
        if pos:
            await sell_position(session, pos, state, "FORCE_CLOSE_4.9s")
            state.positions[direction] = None
    state.force_closing = False
    log.info("✓ All positions closed")


# ── Main Loop ─────────────────────────────────────────────────────────────────
async def run_bot(state: BotState):
    log.info(f"Bot starting | DRY_RUN={DRY_RUN} | SPREAD_ENTRY={SPREAD_ENTRY} | SHARES={SHARES}")

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
                    await evaluate_strategy(session, "up",   state)
                    await evaluate_strategy(session, "down", state)
                    state.record_prices()

                await asyncio.sleep(POLL_MS / 1000)


def start_bot(state: BotState):
    """Entry point called from server.py."""
    asyncio.run(run_bot(state))
