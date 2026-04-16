"""
Shared state between bot thread and Flask dashboard.
"""

import time
from collections import deque
from threading import Lock


class BotState:
    def __init__(self):
        self._lock = Lock()

        # Control
        self.running       = False
        self.force_closing = False

        # Market info
        self.markets        = {}
        self.window_end     = None
        self.seconds_remaining = None

        # Prices & spreads
        self.prices  = {}
        self.spreads = {"a": None, "b": None}  # a=BTC_UP/ETH_DOWN, b=BTC_DOWN/ETH_UP
        self.last_update = None

        # Positions: pair -> dict or None
        self.positions = {"a": None, "b": None}

        # Stats
        self.total_pnl    = 0.0
        self.total_trades = 0
        self.wins         = 0
        self.losses       = 0

        # Real-account tracking (synced from CLOB)
        self.usdc_balance  = None   # actual USDC in proxy wallet
        self.total_bought  = 0.0    # cumulative USDC spent on buys
        self.total_sold    = 0.0    # cumulative USDC received from sells

        # Trade log (last 100)
        self.trade_log = deque(maxlen=100)

        # Price history for chart (last 200 ticks)
        self.price_history = deque(maxlen=200)

    def add_trade_log(self, msg: str):
        with self._lock:
            self.trade_log.appendleft({
                "time": time.strftime("%H:%M:%S"),
                "msg":  msg,
            })

    def record_prices(self):
        """Call after prices update to store history."""
        with self._lock:
            self.price_history.append({
                "ts":       time.time(),
                "btc_up":   self.prices.get("btc_up"),
                "eth_up":   self.prices.get("eth_up"),
                "btc_down": self.prices.get("btc_down"),
                "eth_down": self.prices.get("eth_down"),
                "spread_a": self.spreads.get("a"),
                "spread_b": self.spreads.get("b"),
            })

    def to_dict(self):
        """Serialize for API response."""
        with self._lock:
            return {
                "running":       self.running,
                "force_closing": self.force_closing,
                "window_end":    self.window_end,
                "seconds_remaining": self.seconds_remaining,
                "last_update":   self.last_update,
                "prices": {
                    "btc_up":   self.prices.get("btc_up"),
                    "eth_up":   self.prices.get("eth_up"),
                    "btc_down": self.prices.get("btc_down"),
                    "eth_down": self.prices.get("eth_down"),
                },
                "spreads": {
                    "a": self.spreads.get("a"),
                    "b": self.spreads.get("b"),
                },
                "positions": {
                    "a": self._fmt_pos(self.positions.get("a")),
                    "b": self._fmt_pos(self.positions.get("b")),
                },
                "stats": {
                    "total_pnl":    round(self.total_pnl, 4),
                    "total_trades": self.total_trades,
                    "wins":         self.wins,
                    "losses":       self.losses,
                    "total_bought": round(self.total_bought, 4),
                    "total_sold":   round(self.total_sold, 4),
                },
                "usdc_balance": self.usdc_balance,
                "markets_found": {
                    k: bool(v) for k, v in self.markets.items()
                },
                "trade_log":     list(self.trade_log),
                "price_history": list(self.price_history)[-60:],
            }

    def _fmt_pos(self, pos):
        if not pos:
            return None
        return {
            "entry_spread": round(pos["entry_spread"], 4),
            "entry_time":   pos["entry_time"],
            "tokens": [
                {
                    "key":        t["key"],
                    "shares":     round(t["shares"], 4),
                    "real_shares": round(t.get("real_shares", t["shares"]), 4),
                    "entry_price": round(t["entry_price"], 4),
                    "entry_cost":  round(t["entry_price"] * t["shares"], 4),
                }
                for t in pos["tokens"]
            ],
        }
