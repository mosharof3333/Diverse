"""
Flask server: serves dashboard UI + REST API + starts bot in background thread.
"""

import os
import threading
import logging
from flask import Flask, jsonify, request, render_template_string
from state import BotState
from bot import start_bot
from dashboard import DASHBOARD_HTML

log = logging.getLogger("server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)
state = BotState()
bot_thread = None


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


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "dry_run": os.getenv("DRY_RUN", "true")})


# ── Startup ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    auto_start = os.getenv("AUTO_START", "true").lower() == "true"

    if auto_start:
        log.info("AUTO_START=true — starting bot automatically")
        state.running = True
        bot_thread = threading.Thread(target=start_bot, args=(state,), daemon=True)
        bot_thread.start()

    app.run(host="0.0.0.0", port=port, debug=False)
