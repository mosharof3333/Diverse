import streamlit as st
import pandas as pd
import time
import threading
from datetime import datetime
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCredential, SignatureType
from py_clob_client.constants import POLYGON

# --- CONFIGURATION ---
FUNDER_ADDRESS = "0x43f39b3abdc334623d822e8b25c00813638492fe"

# These should be set in Railway Variables for security
# But for the script to run, we fetch them from the environment
import os
PK = os.getenv("PRIVATE_KEY")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASS = os.getenv("API_PASSPHRASE")

# --- UI SETUP ---
st.set_page_config(page_title="PolyArb BTC/ETH", layout="wide")
st.title("📊 Polymarket 5m Divergence Bot")

# Global state for dashboard
if 'logs' not in st.session_state: st.session_state.logs = []
if 'prices' not in st.session_state: st.session_state.prices = {"btc": 0.5, "eth": 0.5}

# --- TRADING LOGIC ---
def get_5m_slug(coin="btc"):
    """Generates the deterministic slug for the current 5m window"""
    ts = int(time.time() // 300) * 300
    return f"{coin}-updown-5m-{ts}"

def run_bot():
    # Initialize Client
    client = ClobClient(
        host="https://clob.polymarket.com",
        key=PK,
        chain_id=POLYGON,
        funder=FUNDER_ADDRESS,
        signature_type=SignatureType.POLY_PROXY
    )
    client.set_api_creds(ApiCredential(key=API_KEY, secret=API_SECRET, passphrase=API_PASS))

    while True:
        try:
            now = time.time()
            time_until_expiry = 300 - (now % 300)
            
            # 1. FORCE CLOSE AT 4.9 SECONDS
            if time_until_expiry <= 4.9:
                # Cancel all open orders and market sell all positions
                client.cancel_all()
                # (Logic to fetch positions and market sell goes here)
                time.sleep(5)
                continue

            # 2. MARKET DISCOVERY
            btc_slug = get_5m_slug("btc")
            eth_slug = get_5m_slug("eth")
            
            # Fetch prices (Simplified for example)
            # In production, use client.get_market(condition_id)
            btc_price = 0.55 # Placeholder
            eth_price = 0.71 # Placeholder
            diff = btc_price - eth_price

            # 3. STRATEGY EXECUTION
            if btc_price > 0.50 and eth_price > 0.50:
                # Entry: Diff <= -0.15
                if diff <= -0.15:
                    cheapest = "BTC" if btc_price < eth_price else "ETH"
                    # client.create_order(...) for 6 shares
                
                # Rebalance/Exit: Diff >= 0.15
                elif diff >= 0.15:
                    # check profit status then sell or buy opposite
                    pass

            time.sleep(1) # Frequency
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

# --- DASHBOARD RENDER ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("BTC Up", f"${st.session_state.prices['btc']}")
with col2:
    st.metric("ETH Up", f"${st.session_state.prices['eth']}")
with col3:
    st.metric("Current Spread", f"{round(st.session_state.prices['btc'] - st.session_state.prices['eth'], 3)}")

st.subheader("Activity Log")
for log in st.session_state.logs[-5:]:
    st.write(log)

# Start bot in a background thread so it doesn't freeze the website
if st.button("Start Bot"):
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    st.success("Bot Thread Started!")
