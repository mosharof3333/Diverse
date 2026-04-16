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
        self.spreads = {"up": None, "down": None}
        self.last_update = None

        # Positions: direction -> dict or None
        self.positions = {"up": None, "down": None}

        # Stats
        self.total_pnl    = 0.0
        self.total_trades = 0
        self.wins         = 0
        self.losses       = 0

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
                "spread_up":   self.spreads.get("up"),
                "spread_down": self.spreads.get("down"),
            })

    def to_dict(self):
        """Serialize for API response."""
        with self._lock:
            pos_up   = self.positions.get("up")
            pos_down = self.positions.get("down")

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
                    "up":   self.spreads.get("up"),
                    "down": self.spreads.get("down"),
                },
                "positions": {
                    "up":   self._fmt_pos(pos_up),
                    "down": self._fmt_pos(pos_down),
                },
                "stats": {
                    "total_pnl":    round(self.total_pnl, 4),
                    "total_trades": self.total_trades,
                    "wins":         self.wins,
                    "losses":       self.losses,
                },
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
            "side":        pos["side"],
            "price_key":   pos["price_key"],
            "shares":      pos["shares"],
            "entry_price": round(pos["entry_price"], 4),
            "entry_spread": round(pos["entry_spread"], 4),
            "entry_time":  pos["entry_time"],
        }
