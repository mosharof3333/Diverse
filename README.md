# Polymarket 5-Min Spread Bot

BTC/ETH cross-market spread trading bot with live dashboard.

---

## What This Bot Does

- Watches BTC Up, BTC Down, ETH Up, ETH Down on Polymarket 5-minute markets
- When BTC and ETH prices diverge by ≥ 0.15 (and both > 0.50), buys the cheaper side (6 shares)
- Exits when spread closes +0.15 in your favor (profit) or rebalances if not profitable
- **Force closes ALL positions at 4.9 seconds before window end, every time**
- Beautiful live dashboard showing prices, spreads, positions, PnL, and trade log

---

## Deploy in 10 Minutes (No Coding Required)

### Step 1 — Get the code onto GitHub

1. Go to [github.com](https://github.com) and create a free account (if you don't have one)
2. Click the **+** button (top right) → **New repository**
3. Name it: `polymarket-bot`
4. Keep it **Private**
5. Click **Create repository**
6. Click **uploading an existing file** link on the empty repo page
7. Upload ALL these files at once:
   - `bot.py`
   - `server.py`
   - `state.py`
   - `dashboard.py`
   - `requirements.txt`
   - `Procfile`
   - `.gitignore`
8. Click **Commit changes**

---

### Step 2 — Deploy on Railway

1. Go to [railway.app](https://railway.app) and sign up with your GitHub account
2. Click **New Project**
3. Click **Deploy from GitHub repo**
4. Select your `polymarket-bot` repository
5. Railway will detect it automatically and start deploying

---

### Step 3 — Set Environment Variables on Railway

1. In your Railway project, click on your service
2. Click the **Variables** tab
3. Add these one by one (click **+ New Variable** for each):

| Variable | Value | Notes |
|----------|-------|-------|
| `DRY_RUN` | `true` | Keep true until you're ready for real trading |
| `AUTO_START` | `true` | Bot starts automatically |
| `SPREAD_ENTRY` | `0.15` | Entry spread threshold |
| `SPREAD_EXIT` | `0.15` | Exit spread threshold |
| `MIN_PRICE` | `0.50` | Minimum price filter |
| `SHARES` | `6` | Shares per trade |
| `FORCE_CLOSE_SEC` | `4.9` | Force close seconds |
| `POLL_MS` | `500` | Poll interval |

4. Click **Deploy** (Railway redeploys automatically when you save variables)

---

### Step 4 — Open Your Dashboard

1. In Railway, click your service → **Settings** tab
2. Under **Networking**, click **Generate Domain**
3. Copy the URL (looks like `https://polymarket-bot-xxxx.railway.app`)
4. Open it in your browser — you'll see the live dashboard!

---

### Step 5 — Go Live (Real Trading)

When you're ready to trade real money:

1. Go to [polymarket.com](https://polymarket.com) → sign in
2. Click your profile → **API Keys** → generate a key
3. In Railway Variables, set:
   - `DRY_RUN` → `false`
   - `POLY_API_KEY` → your key
   - `POLY_PRIVATE_KEY` → your private key
4. Railway will redeploy automatically

---

## Dashboard Guide

| Section | What It Shows |
|---------|--------------|
| **Price Cards** | Live buy prices for BTC/ETH Up/Down |
| **Spread Meter** | Current spread with entry threshold bar |
| **Window Timer** | Countdown ring to window end |
| **Positions** | Open trades with entry price and duration |
| **Stats Bar** | Total PnL, trade count, wins/losses |
| **Price Chart** | BTC Up vs ETH Up price history |
| **Trade Log** | Every action the bot took |

---

## Strategy Summary

```
UP MARKETS (BTC Up vs ETH Up):
  Entry:  |btcUp - ethUp| >= 0.15  AND  both > 0.50
  Trade:  Buy 6 shares of the cheaper one
  Exit A: Spread closes 0.15 in favor → SELL (profit)
  Exit B: Spread closes 0.15 against  → BUY opposite 6 shares (rebalance)

DOWN MARKETS (BTC Down vs ETH Down):
  Same logic, mirrored

ALWAYS: Force close ALL positions at 4.9s before window ends
```

---

## Troubleshooting

**Bot not finding markets?**
→ 5-min markets rotate. Wait for a fresh window start and check the dashboard.

**Dashboard shows all dashes?**
→ Click ▶ START on the dashboard, or set `AUTO_START=true` in Railway variables.

**Railway build failing?**
→ Make sure all 7 files were uploaded. Check Railway logs under the **Deploy** tab.
