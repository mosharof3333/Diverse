DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Polymarket Spread Bot</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root {
  --bg:      #060810;
  --panel:   #0b0d14;
  --border:  #151928;
  --border2: #1e2235;
  --green:   #00e676;
  --red:     #ff1744;
  --blue:    #2979ff;
  --yellow:  #ffea00;
  --orange:  #ff6d00;
  --cyan:    #00e5ff;
  --text:    #cdd6f4;
  --muted:   #45475a;
  --btc:     #f7931a;
  --eth:     #627eea;
}
*{margin:0;padding:0;box-sizing:border-box;}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:'Share Tech Mono',monospace;overflow-x:hidden;}

/* scanlines effect */
body::before{
  content:'';position:fixed;top:0;left:0;right:0;bottom:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.03) 2px,rgba(0,0,0,0.03) 4px);
  pointer-events:none;z-index:9999;
}

/* ── Header ── */
.header{
  display:flex;align-items:center;justify-content:space-between;
  padding:1rem 1.5rem;
  border-bottom:1px solid var(--border2);
  background:linear-gradient(90deg,#060810,#0b0d18,#060810);
  position:sticky;top:0;z-index:100;
}
.logo{
  font-family:'Orbitron',monospace;font-weight:900;font-size:1.1rem;
  color:var(--green);letter-spacing:0.15em;
  text-shadow:0 0 20px rgba(0,230,118,0.5);
}
.logo span{color:var(--muted);}
.header-right{display:flex;align-items:center;gap:1rem;}
.mode-badge{
  font-size:0.65rem;font-weight:700;padding:0.25rem 0.6rem;border-radius:2px;letter-spacing:0.1em;
}
.mode-badge.dry{background:#ffea0022;color:var(--yellow);border:1px solid #ffea0055;}
.mode-badge.live{background:#00e67622;color:var(--green);border:1px solid #00e67655;}

.btn{
  font-family:'Share Tech Mono',monospace;font-size:0.75rem;font-weight:700;
  padding:0.4rem 1rem;border:none;cursor:pointer;border-radius:2px;
  transition:all 0.15s;letter-spacing:0.05em;
}
.btn-start{background:var(--green);color:#000;}
.btn-start:hover{box-shadow:0 0 15px rgba(0,230,118,0.5);}
.btn-stop{background:var(--red);color:#fff;}
.btn-stop:hover{box-shadow:0 0 15px rgba(255,23,68,0.4);}
.btn:disabled{opacity:0.4;cursor:not-allowed;}

/* ── Layout ── */
.main{padding:1rem 1.5rem;display:grid;gap:1rem;}

/* top row: 4 price cards */
.price-row{display:grid;grid-template-columns:repeat(4,1fr);gap:0.75rem;}

/* mid row: spread + timer + positions */
.mid-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.75rem;}

/* bottom row: chart + log */
.bot-row{display:grid;grid-template-columns:2fr 1fr;gap:0.75rem;}

@media(max-width:1100px){
  .price-row{grid-template-columns:repeat(2,1fr);}
  .mid-row{grid-template-columns:1fr 1fr;}
  .bot-row{grid-template-columns:1fr;}
}
@media(max-width:600px){
  .price-row{grid-template-columns:1fr 1fr;}
  .mid-row{grid-template-columns:1fr;}
}

/* ── Panel ── */
.panel{
  background:var(--panel);
  border:1px solid var(--border2);
  border-radius:4px;
  padding:0.85rem;
  position:relative;overflow:hidden;
}
.panel::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
}
.panel.green::before{background:linear-gradient(90deg,transparent,var(--green),transparent);}
.panel.red::before{background:linear-gradient(90deg,transparent,var(--red),transparent);}
.panel.blue::before{background:linear-gradient(90deg,transparent,var(--blue),transparent);}
.panel.yellow::before{background:linear-gradient(90deg,transparent,var(--yellow),transparent);}
.panel.orange::before{background:linear-gradient(90deg,transparent,var(--orange),transparent);}
.panel.cyan::before{background:linear-gradient(90deg,transparent,var(--cyan),transparent);}

.panel-label{
  font-size:0.6rem;letter-spacing:0.18em;color:var(--muted);text-transform:uppercase;margin-bottom:0.4rem;
}

/* ── Price Card ── */
.price-card .asset-row{display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem;}
.asset-tag{
  font-family:'Orbitron',monospace;font-size:0.7rem;font-weight:700;
  padding:0.15rem 0.4rem;border-radius:2px;
}
.tag-btc{background:#f7931a22;color:var(--btc);border:1px solid #f7931a55;}
.tag-eth{background:#627eea22;color:var(--eth);border:1px solid #627eea55;}
.dir-tag{font-size:0.65rem;padding:0.1rem 0.35rem;border-radius:2px;}
.dir-up{background:#00e67622;color:var(--green);border:1px solid #00e67655;}
.dir-down{background:#ff174422;color:var(--red);border:1px solid #ff174455;}

.price-big{
  font-family:'Orbitron',monospace;font-size:1.5rem;font-weight:900;
  line-height:1;margin-bottom:0.2rem;
}
.price-change{font-size:0.65rem;}
.price-change.pos{color:var(--green);}
.price-change.neg{color:var(--red);}

/* ── Spread Meter ── */
.spread-val{
  font-family:'Orbitron',monospace;font-size:1.8rem;font-weight:900;
  color:var(--cyan);text-shadow:0 0 15px rgba(0,229,255,0.4);
}
.spread-bar-wrap{margin-top:0.5rem;}
.spread-bar-bg{
  height:6px;background:var(--border2);border-radius:3px;
  overflow:hidden;margin-bottom:0.3rem;
}
.spread-bar-fill{
  height:100%;border-radius:3px;transition:width 0.3s;
  background:linear-gradient(90deg,var(--blue),var(--cyan));
}
.spread-bar-fill.triggered{background:linear-gradient(90deg,var(--green),var(--cyan));}
.spread-threshold{display:flex;justify-content:space-between;font-size:0.6rem;color:var(--muted);}

/* ── Timer ── */
.timer-ring-wrap{display:flex;justify-content:center;margin:0.3rem 0;}
.timer-svg{transform:rotate(-90deg);}
.timer-track{fill:none;stroke:var(--border2);stroke-width:6;}
.timer-prog{fill:none;stroke-width:6;stroke-linecap:round;transition:stroke-dashoffset 0.5s,stroke 0.5s;}
.timer-text{
  position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  font-family:'Orbitron',monospace;font-size:1.4rem;font-weight:900;
  text-align:center;
}
.timer-sub{font-size:0.55rem;color:var(--muted);letter-spacing:0.1em;}
.timer-wrap{position:relative;display:flex;align-items:center;justify-content:center;}

/* ── Position Card ── */
.pos-empty{color:var(--muted);font-size:0.72rem;margin-top:0.3rem;}
.pos-side{
  font-family:'Orbitron',monospace;font-size:0.85rem;font-weight:700;margin-bottom:0.3rem;
}
.pos-row{display:flex;justify-content:space-between;font-size:0.68rem;margin-top:0.2rem;}
.pos-row .label{color:var(--muted);}
.pnl-pos{color:var(--green);}
.pnl-neg{color:var(--red);}

/* ── Stats Bar ── */
.stats-row{display:grid;grid-template-columns:repeat(6,1fr);gap:0.75rem;}
@media(max-width:1200px){.stats-row{grid-template-columns:repeat(3,1fr);}}
@media(max-width:700px){.stats-row{grid-template-columns:repeat(2,1fr);}}
.stat-box{background:var(--panel);border:1px solid var(--border2);border-radius:4px;padding:0.6rem 0.85rem;}
.stat-label{font-size:0.58rem;color:var(--muted);letter-spacing:0.12em;text-transform:uppercase;}
.stat-val{font-family:'Orbitron',monospace;font-size:1.1rem;font-weight:700;margin-top:0.15rem;}
.stat-val.pos{color:var(--green);}
.stat-val.neg{color:var(--red);}
.stat-val.neutral{color:var(--cyan);}

/* ── Chart ── */
.chart-wrap{height:220px;position:relative;}

/* ── Trade Log ── */
.log-scroll{height:220px;overflow-y:auto;font-size:0.65rem;line-height:1.9;}
.log-scroll::-webkit-scrollbar{width:3px;}
.log-scroll::-webkit-scrollbar-track{background:transparent;}
.log-scroll::-webkit-scrollbar-thumb{background:var(--border2);}
.log-entry{display:flex;gap:0.5rem;border-bottom:1px solid var(--border);padding:0.1rem 0;}
.log-time{color:var(--muted);flex-shrink:0;}
.log-msg.buy{color:var(--green);}
.log-msg.sell{color:var(--red);}
.log-msg.info{color:var(--cyan);}
.log-msg.warn{color:var(--yellow);}

/* ── Markets Status ── */
.mkt-status{display:flex;gap:0.5rem;flex-wrap:wrap;margin-top:0.4rem;}
.mkt-pill{
  font-size:0.6rem;padding:0.15rem 0.4rem;border-radius:2px;
  border:1px solid;
}
.mkt-pill.found{background:#00e67611;color:var(--green);border-color:#00e67633;}
.mkt-pill.missing{background:#ff174411;color:var(--red);border-color:#ff174433;}

/* ── Pulse dot ── */
.dot{width:7px;height:7px;border-radius:50%;display:inline-block;margin-right:5px;}
.dot.live{background:var(--green);box-shadow:0 0 6px var(--green);animation:blink 1.2s infinite;}
.dot.idle{background:var(--muted);}
.dot.warn{background:var(--yellow);animation:blink 0.5s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}

/* ── Force close alert ── */
.force-banner{
  display:none;
  background:#ff174422;border:1px solid var(--red);border-radius:4px;
  padding:0.5rem 1rem;text-align:center;
  font-family:'Orbitron',monospace;font-size:0.8rem;color:var(--red);
  letter-spacing:0.1em;margin-bottom:0.75rem;
  animation:blink 0.4s infinite;
}
.force-banner.visible{display:block;}
</style>
</head>
<body>

<!-- ── Header ── -->
<div class="header">
  <div class="logo">POLY<span>SPREAD</span>BOT <span style="font-size:0.6rem;color:var(--muted)">v1.0</span></div>
  <div class="header-right">
    <a href="/trade" style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;color:var(--cyan);text-decoration:none;padding:0.4rem 0.9rem;border:1px solid var(--cyan);border-radius:2px;letter-spacing:0.05em;">⚡ MANUAL TRADE</a>
    <span id="modeBadge" class="mode-badge dry">DRY RUN</span>
    <span><span class="dot idle" id="statusDot"></span><span id="statusText" style="font-size:0.72rem">IDLE</span></span>
    <button class="btn btn-start" id="startBtn" onclick="startBot()">▶ START</button>
    <button class="btn btn-stop"  id="stopBtn"  onclick="stopBot()" disabled>■ STOP</button>
  </div>
</div>

<!-- ── Main ── -->
<div class="main">

  <!-- Force Close Banner -->
  <div class="force-banner" id="forceBanner">⚡ FORCE CLOSING ALL POSITIONS — 4.9s WINDOW END</div>

  <!-- Stats Row -->
  <div class="stats-row">
    <div class="stat-box">
      <div class="stat-label">Total PnL</div>
      <div class="stat-val" id="statPnl">$0.0000</div>
    </div>
    <div class="stat-box">
      <div class="stat-label">Wins / Losses</div>
      <div class="stat-val neutral" id="statWL">0 / 0</div>
    </div>
    <div class="stat-box">
      <div class="stat-label">Bought / Sold (USDC)</div>
      <div class="stat-val neutral" id="statBoughtSold">$0 / $0</div>
    </div>
    <div class="stat-box">
      <div class="stat-label">Wallet Balance</div>
      <div class="stat-val neutral" id="statWallet">—</div>
    </div>
    <div class="stat-box">
      <div class="stat-label">Trades</div>
      <div class="stat-val neutral" id="statTrades">0</div>
    </div>
    <div class="stat-box">
      <div class="stat-label">Markets</div>
      <div id="mktStatus" class="mkt-status">
        <span class="mkt-pill missing">btc_up</span>
        <span class="mkt-pill missing">btc_down</span>
        <span class="mkt-pill missing">eth_up</span>
        <span class="mkt-pill missing">eth_down</span>
      </div>
    </div>
  </div>

  <!-- Price Row -->
  <div class="price-row">
    <div class="panel green price-card" id="card-btc-up">
      <div class="panel-label">Buy Price</div>
      <div class="asset-row">
        <span class="asset-tag tag-btc">BTC</span>
        <span class="dir-tag dir-up">UP</span>
      </div>
      <div class="price-big" id="p-btc-up">—</div>
      <div class="price-change" id="pc-btc-up">—</div>
    </div>
    <div class="panel red price-card" id="card-btc-down">
      <div class="panel-label">Buy Price</div>
      <div class="asset-row">
        <span class="asset-tag tag-btc">BTC</span>
        <span class="dir-tag dir-down">DOWN</span>
      </div>
      <div class="price-big" id="p-btc-down">—</div>
      <div class="price-change" id="pc-btc-down">—</div>
    </div>
    <div class="panel green price-card" id="card-eth-up">
      <div class="panel-label">Buy Price</div>
      <div class="asset-row">
        <span class="asset-tag tag-eth">ETH</span>
        <span class="dir-tag dir-up">UP</span>
      </div>
      <div class="price-big" id="p-eth-up">—</div>
      <div class="price-change" id="pc-eth-up">—</div>
    </div>
    <div class="panel red price-card" id="card-eth-down">
      <div class="panel-label">Buy Price</div>
      <div class="asset-row">
        <span class="asset-tag tag-eth">ETH</span>
        <span class="dir-tag dir-down">DOWN</span>
      </div>
      <div class="price-big" id="p-eth-down">—</div>
      <div class="price-change" id="pc-eth-down">—</div>
    </div>
  </div>

  <!-- Mid Row -->
  <div class="mid-row">

    <!-- Spread Pair A -->
    <div class="panel cyan">
      <div class="panel-label">Pair A — BTC&#x2191; + ETH&#x2193; Spread</div>
      <div class="spread-val" id="spreadA">0.000</div>
      <div class="spread-bar-wrap">
        <div class="spread-bar-bg"><div class="spread-bar-fill" id="spreadABar" style="width:0%"></div></div>
        <div class="spread-threshold"><span>0.00</span><span>0.10 / 0.15 / 0.30</span><span>0.30</span></div>
      </div>
    </div>

    <!-- Timer -->
    <div class="panel blue">
      <div class="panel-label">Window Timer</div>
      <div class="timer-wrap" style="height:110px;">
        <svg class="timer-svg" width="100" height="100" viewBox="0 0 100 100">
          <circle class="timer-track" cx="50" cy="50" r="44"/>
          <circle class="timer-prog" id="timerCircle" cx="50" cy="50" r="44"
            stroke="var(--blue)"
            stroke-dasharray="276.46"
            stroke-dashoffset="0"/>
        </svg>
        <div class="timer-text">
          <div id="timerVal" style="color:var(--cyan)">—</div>
          <div class="timer-sub">SECONDS</div>
        </div>
      </div>
    </div>

    <!-- Spread Pair B -->
    <div class="panel orange">
      <div class="panel-label">Pair B — BTC&#x2193; + ETH&#x2191; Spread</div>
      <div class="spread-val" style="color:var(--orange)" id="spreadB">0.000</div>
      <div class="spread-bar-wrap">
        <div class="spread-bar-bg"><div class="spread-bar-fill" id="spreadBBar" style="width:0%;background:linear-gradient(90deg,var(--orange),var(--yellow))"></div></div>
        <div class="spread-threshold"><span>0.00</span><span>0.10 / 0.15 / 0.30</span><span>0.30</span></div>
      </div>
    </div>

  </div>

  <!-- Positions Row -->
  <div class="mid-row">
    <div class="panel yellow">
      <div class="panel-label">Pair A — BTC&#x2191; + ETH&#x2193;</div>
      <div id="posA"><div class="pos-empty">No position open</div></div>
    </div>
    <div class="panel">
      <div class="panel-label">Last Signal</div>
      <div id="lastSignal" style="font-size:0.7rem;color:var(--muted);margin-top:0.3rem">—</div>
    </div>
    <div class="panel yellow">
      <div class="panel-label">Pair B — BTC&#x2193; + ETH&#x2191;</div>
      <div id="posB"><div class="pos-empty">No position open</div></div>
    </div>
  </div>

  <!-- Chart + Log -->
  <div class="bot-row">
    <div class="panel blue">
      <div class="panel-label">Price History — BTC Up vs ETH Up</div>
      <div class="chart-wrap">
        <canvas id="priceChart"></canvas>
      </div>
    </div>
    <div class="panel">
      <div class="panel-label">Trade Log</div>
      <div class="log-scroll" id="tradeLog">
        <div style="color:var(--muted);font-size:0.65rem;margin-top:0.3rem">No trades yet…</div>
      </div>
    </div>
  </div>

</div><!-- /main -->

<script>
// ── Chart Setup ──────────────────────────────────────────────────────────────
const ctx = document.getElementById('priceChart').getContext('2d');
const priceChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [
      {
        label: 'BTC Up',
        data: [],
        borderColor: '#f7931a',
        backgroundColor: 'rgba(247,147,26,0.06)',
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0.3,
        fill: false,
      },
      {
        label: 'ETH Up',
        data: [],
        borderColor: '#627eea',
        backgroundColor: 'rgba(98,126,234,0.06)',
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0.3,
        fill: false,
      },
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 0 },
    plugins: {
      legend: {
        labels: { color: '#45475a', font: { family: 'Share Tech Mono', size: 10 }, boxWidth: 10 }
      }
    },
    scales: {
      x: { display: false },
      y: {
        min: 0, max: 1,
        grid: { color: '#151928' },
        ticks: { color: '#45475a', font: { family: 'Share Tech Mono', size: 9 } }
      }
    }
  }
});

// ── State ─────────────────────────────────────────────────────────────────────
let prevPrices = {};

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmt(v) { return v != null ? parseFloat(v).toFixed(3) : '—'; }
function fmtPnl(v) { return (v >= 0 ? '+' : '') + parseFloat(v).toFixed(4); }

function setPrice(key, val) {
  let el = document.getElementById('p-' + key.replace('_', '-'));
  if (!el) return;
  let prev = prevPrices[key];
  el.textContent = fmt(val);
  el.style.color = val == null ? 'var(--muted)' : (prev == null ? 'var(--text)' : val > prev ? 'var(--green)' : val < prev ? 'var(--red)' : 'var(--text)');

  let chEl = document.getElementById('pc-' + key.replace('_', '-'));
  if (chEl && prev != null && val != null) {
    let diff = val - prev;
    chEl.textContent = (diff >= 0 ? '+' : '') + diff.toFixed(4);
    chEl.className = 'price-change ' + (diff > 0 ? 'pos' : diff < 0 ? 'neg' : '');
  }
}

function setSpread(pair, val) {
  let idVal = pair === 'a' ? 'spreadA' : 'spreadB';
  let idBar = pair === 'a' ? 'spreadABar' : 'spreadBBar';
  let el = document.getElementById(idVal);
  let bar = document.getElementById(idBar);
  if (!el || !bar) return;
  if (val == null) { el.textContent = '0.000'; bar.style.width = '0%'; return; }
  el.textContent = parseFloat(val).toFixed(3);
  let pct = Math.min(100, (val / 0.30) * 100);
  bar.style.width = pct + '%';
  bar.className = 'spread-bar-fill' + (val >= 0.10 ? ' triggered' : '');
}

function renderPos(pair, pos) {
  let el = document.getElementById('pos' + pair.toUpperCase());
  if (!el) return;
  if (!pos || !pos.tokens) { el.innerHTML = '<div class="pos-empty">No position open</div>'; return; }

  let now = Date.now() / 1000;
  let dur = pos.entry_time ? Math.floor(now - pos.entry_time) : 0;

  let tokensHtml = pos.tokens.map(t => {
    let match = t.real_shares === t.shares;
    let col = match ? 'var(--green)' : 'var(--yellow)';
    return `
      <div style="margin-top:0.4rem;border-top:1px solid var(--border);padding-top:0.3rem">
        <div class="pos-side" style="color:var(--cyan);font-size:0.75rem">${t.key.toUpperCase()}</div>
        <div class="pos-row"><span class="label">Shares</span><span>${t.shares}</span></div>
        <div class="pos-row"><span class="label">Chain</span><span style="color:${col}">${t.real_shares}</span></div>
        <div class="pos-row"><span class="label">Entry</span><span>${parseFloat(t.entry_price).toFixed(4)}</span></div>
        <div class="pos-row"><span class="label">Cost</span><span>$${parseFloat(t.entry_cost).toFixed(4)}</span></div>
      </div>`;
  }).join('');

  el.innerHTML = `
    <div class="pos-row"><span class="label">Spread @ Entry</span><span>${parseFloat(pos.entry_spread).toFixed(4)}</span></div>
    <div class="pos-row"><span class="label">Duration</span><span>${dur}s</span></div>
    ${tokensHtml}
  `;
}

function renderTimer(secs) {
  let el = document.getElementById('timerVal');
  let circ = document.getElementById('timerCircle');
  if (!el || !circ) return;

  if (secs == null || secs < 0) {
    el.textContent = '—';
    circ.style.strokeDashoffset = '0';
    circ.style.stroke = 'var(--blue)';
    return;
  }

  let s = Math.max(0, secs);
  el.textContent = s.toFixed(1);
  let total = 300; // 5 minutes
  let pct = s / total;
  let circumference = 276.46;
  circ.style.strokeDashoffset = circumference * (1 - pct);
  circ.style.stroke = s <= 10 ? 'var(--red)' : s <= 30 ? 'var(--yellow)' : 'var(--blue)';
  el.style.color = s <= 10 ? 'var(--red)' : s <= 30 ? 'var(--yellow)' : 'var(--cyan)';
}

function updateChart(history) {
  if (!history || history.length === 0) return;
  let labels = history.map((_, i) => i);
  let btc = history.map(h => h.btc_up);
  let eth = history.map(h => h.eth_up);
  priceChart.data.labels = labels;
  priceChart.data.datasets[0].data = btc;
  priceChart.data.datasets[1].data = eth;
  priceChart.update('none');
}

function renderLog(entries) {
  let el = document.getElementById('tradeLog');
  if (!entries || entries.length === 0) return;
  el.innerHTML = entries.map(e => {
    let cls = e.msg.includes('BUY') ? 'buy' : e.msg.includes('SELL') ? 'sell' : e.msg.includes('REBALANCE') ? 'warn' : 'info';
    return `<div class="log-entry"><span class="log-time">${e.time}</span><span class="log-msg ${cls}">${e.msg}</span></div>`;
  }).join('');
}

function renderMarkets(mf) {
  let el = document.getElementById('mktStatus');
  if (!el || !mf) return;
  el.innerHTML = Object.entries(mf).map(([k, v]) =>
    `<span class="mkt-pill ${v ? 'found' : 'missing'}">${k}</span>`
  ).join('');
}

// ── Polling ──────────────────────────────────────────────────────────────────
async function poll() {
  try {
    let r = await fetch('/api/state');
    let d = await r.json();

    // Status dot + button state
    let dot = document.getElementById('statusDot');
    let txt = document.getElementById('statusText');
    if (d.running) {
      dot.className = d.force_closing ? 'dot warn' : 'dot live';
      txt.textContent = d.force_closing ? 'FORCE CLOSE' : 'LIVE';
    } else {
      dot.className = 'dot idle'; txt.textContent = 'IDLE';
    }
    document.getElementById('startBtn').disabled = d.running;
    document.getElementById('stopBtn').disabled = !d.running;

    document.getElementById('forceBanner').className = 'force-banner' + (d.force_closing ? ' visible' : '');

    // DRY RUN badge (fetch from /api/health first tick)
    if (d.prices) {
      ['btc_up','btc_down','eth_up','eth_down'].forEach(k => setPrice(k, d.prices[k]));
      prevPrices = { ...d.prices };
    }

    setSpread('a', d.spreads?.a);
    setSpread('b', d.spreads?.b);
    renderTimer(d.seconds_remaining);
    renderPos('a', d.positions?.a);
    renderPos('b', d.positions?.b);

    // Stats
    let pnl = d.stats?.total_pnl ?? 0;
    let pnlEl = document.getElementById('statPnl');
    pnlEl.textContent = '$' + fmtPnl(pnl);
    pnlEl.className = 'stat-val ' + (pnl > 0 ? 'pos' : pnl < 0 ? 'neg' : 'neutral');
    document.getElementById('statTrades').textContent = d.stats?.total_trades ?? 0;
    document.getElementById('statWL').textContent = `${d.stats?.wins ?? 0} / ${d.stats?.losses ?? 0}`;

    // Bought / Sold
    let bought = d.stats?.total_bought ?? 0;
    let sold   = d.stats?.total_sold   ?? 0;
    document.getElementById('statBoughtSold').textContent =
      '$' + parseFloat(bought).toFixed(2) + ' / $' + parseFloat(sold).toFixed(2);

    // Wallet balance (real USDC from chain)
    let walletEl = document.getElementById('statWallet');
    if (d.usdc_balance != null) {
      walletEl.textContent = '$' + parseFloat(d.usdc_balance).toFixed(2);
      walletEl.className = 'stat-val ' + (d.usdc_balance > 0 ? 'pos' : 'neutral');
    } else {
      walletEl.textContent = '—';
      walletEl.className = 'stat-val neutral';
    }

    renderMarkets(d.markets_found);
    updateChart(d.price_history);
    renderLog(d.trade_log);

    // Last signal
    if (d.spreads?.a != null || d.spreads?.b != null) {
      let sa = parseFloat(d.spreads?.a || 0);
      let sb = parseFloat(d.spreads?.b || 0);
      let sig = sa >= 0.10 ? `Pair A triggered (${sa.toFixed(3)})` : sb >= 0.10 ? `Pair B triggered (${sb.toFixed(3)})` : 'Watching…';
      document.getElementById('lastSignal').textContent = sig;
      document.getElementById('lastSignal').style.color = (sa >= 0.10 || sb >= 0.10) ? 'var(--green)' : 'var(--muted)';
    }

  } catch(e) { /* ignore */ }
}

async function startBot() {
  await fetch('/api/start', { method: 'POST' });
  document.getElementById('startBtn').disabled = true;
  document.getElementById('stopBtn').disabled = false;
}

async function stopBot() {
  await fetch('/api/stop', { method: 'POST' });
  document.getElementById('startBtn').disabled = false;
  document.getElementById('stopBtn').disabled = true;
}

// Check dry run mode
fetch('/api/health').then(r => r.json()).then(d => {
  let b = document.getElementById('modeBadge');
  if (d.dry_run === 'false') { b.textContent = 'LIVE TRADING'; b.className = 'mode-badge live'; }
});

setInterval(poll, 600);
poll();
</script>
</body>
</html>
"""

TRADING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Manual Trading — Polymarket</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#060810;--panel:#0b0d14;--border:#151928;--border2:#1e2235;
  --green:#00e676;--red:#ff1744;--blue:#2979ff;--yellow:#ffea00;
  --cyan:#00e5ff;--text:#cdd6f4;--muted:#45475a;--btc:#f7931a;--eth:#627eea;
}
*{margin:0;padding:0;box-sizing:border-box;}
html,body{background:var(--bg);color:var(--text);font-family:"Share Tech Mono",monospace;min-height:100%;}
body::before{content:"";position:fixed;inset:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.03) 2px,rgba(0,0,0,.03) 4px);
  pointer-events:none;z-index:9999;}

/* header */
.hdr{display:flex;align-items:center;justify-content:space-between;
  padding:.8rem 1.2rem;border-bottom:1px solid var(--border2);
  background:linear-gradient(90deg,#060810,#0b0d18,#060810);position:sticky;top:0;z-index:100;}
.logo{font-family:"Orbitron",monospace;font-weight:900;font-size:1rem;
  color:var(--cyan);letter-spacing:.15em;text-shadow:0 0 16px rgba(0,229,255,.5);}
.logo span{color:var(--muted);}
.hdr-right{display:flex;align-items:center;gap:.8rem;}
.back{color:var(--muted);text-decoration:none;font-size:.75rem;
  padding:.35rem .8rem;border:1px solid var(--border2);border-radius:4px;}
.back:hover{color:var(--cyan);border-color:var(--cyan);}
.live-dot{width:8px;height:8px;border-radius:50%;background:var(--muted);
  display:inline-block;margin-right:.4rem;transition:background .3s;}
.live-dot.on{background:var(--green);box-shadow:0 0 6px var(--green);animation:blink 1.5s infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:.3;}}
#liveLabel{font-size:.72rem;}

/* stats bar */
.stats{display:flex;flex-wrap:wrap;gap:.6rem 1.2rem;
  padding:.6rem 1.2rem;background:var(--panel);border-bottom:1px solid var(--border);}
.stat{display:flex;flex-direction:column;gap:.1rem;}
.sl{font-size:.58rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;}
.sv{font-size:.9rem;font-weight:700;}
.sv.c{color:var(--cyan);} .sv.g{color:var(--green);} .sv.r{color:var(--red);}
.sv.y{color:var(--yellow);}

/* window bar */
.wbar{display:flex;align-items:center;gap:.8rem;
  padding:.4rem 1.2rem;background:#080a10;border-bottom:1px solid var(--border);font-size:.75rem;}
.wlabel{color:var(--muted);}
.wtrack{flex:1;height:4px;background:var(--border);border-radius:2px;overflow:hidden;}
.wfill{height:100%;background:linear-gradient(90deg,var(--green),var(--yellow));transition:width .5s;}
.wtimer{font-family:"Orbitron",monospace;color:var(--yellow);min-width:44px;text-align:right;}

/* main grid */
.main{padding:1rem 1.2rem;display:grid;gap:.9rem;}
.pairs{display:grid;grid-template-columns:1fr 1fr;gap:.9rem;}
@media(max-width:780px){.pairs{grid-template-columns:1fr;}}

/* pair card */
.pcard{background:var(--panel);border:1px solid var(--border2);border-radius:8px;overflow:hidden;}
.pcard.a{border-top:2px solid var(--btc);}
.pcard.b{border-top:2px solid var(--eth);}
.pcard-hdr{display:flex;justify-content:space-between;align-items:center;
  padding:.6rem .9rem;border-bottom:1px solid var(--border);}
.pcard-title{font-family:"Orbitron",monospace;font-size:.75rem;letter-spacing:.08em;}
.pcard.a .pcard-title{color:var(--btc);}
.pcard.b .pcard-title{color:var(--eth);}
.pcard-body{padding:.9rem;}

/* token rows inside pair card */
.trow{display:flex;align-items:center;justify-content:space-between;
  padding:.4rem 0;border-bottom:1px solid var(--border);}
.trow:last-of-type{border:none;}
.tname{font-size:.78rem;min-width:100px;}
.badge{display:inline-block;padding:.1rem .4rem;border-radius:3px;font-size:.65rem;font-weight:700;margin-right:.3rem;}
.btc-up{background:rgba(247,147,26,.15);color:var(--btc);border:1px solid rgba(247,147,26,.3);}
.btc-dn{background:rgba(247,147,26,.1);color:#c07010;border:1px solid rgba(247,147,26,.2);}
.eth-up{background:rgba(98,126,234,.15);color:var(--eth);border:1px solid rgba(98,126,234,.3);}
.eth-dn{background:rgba(98,126,234,.1);color:#4a5fc0;border:1px solid rgba(98,126,234,.2);}
.tprice{font-size:1.05rem;font-weight:700;min-width:65px;text-align:right;}
.twallet{font-size:.7rem;color:var(--muted);min-width:90px;text-align:right;}
.twallet.has{color:var(--yellow);font-weight:700;}

/* gap box */
.gapbox{display:flex;justify-content:space-between;align-items:center;
  margin:.7rem 0;padding:.55rem .7rem;background:#0d0f18;border-radius:6px;border:1px solid var(--border);}
.glabel{font-size:.6rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;}
.gvalue{font-size:1.2rem;font-family:"Orbitron",monospace;font-weight:700;color:var(--yellow);}
.gcol{display:flex;flex-direction:column;gap:.15rem;}

/* threshold bar */
.tbar{margin:.4rem 0 .7rem;}
.tbar-labels{display:flex;justify-content:space-between;font-size:.58rem;color:var(--muted);margin-bottom:.2rem;}
.tbar-track{height:5px;background:var(--border);border-radius:3px;position:relative;}
.tbar-fill{height:100%;border-radius:3px;background:linear-gradient(90deg,var(--green),var(--yellow),var(--red));transition:width .3s;}
.tm{position:absolute;top:-3px;width:2px;height:11px;border-radius:1px;}
.tm1{background:var(--green);left:33.3%;}
.tm2{background:var(--yellow);left:50%;}
.tm3{background:var(--red);left:100%;}

/* buy pair button */
.buypair{width:100%;padding:.65rem;font-family:"Orbitron",monospace;font-size:.8rem;
  font-weight:700;letter-spacing:.08em;border:none;border-radius:6px;cursor:pointer;
  transition:all .15s;margin-top:.3rem;}
.pcard.a .buypair{background:linear-gradient(135deg,var(--btc),#c06010);color:#000;}
.pcard.b .buypair{background:linear-gradient(135deg,var(--eth),#3a4faa);color:#fff;}
.buypair:hover{transform:translateY(-1px);box-shadow:0 4px 16px rgba(0,0,0,.5);}
.buypair:active{transform:none;}
.buypair:disabled{opacity:.4;cursor:not-allowed;transform:none;}

/* shares input */
.shares-row{display:flex;align-items:center;gap:.8rem;flex-wrap:wrap;
  background:var(--panel);border:1px solid var(--border2);border-radius:8px;padding:.7rem 1rem;}
.shares-label{font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;}
.shares-input{background:#0d0f18;border:1px solid var(--border2);color:var(--text);
  padding:.35rem .5rem;border-radius:4px;font-family:inherit;font-size:1rem;
  width:72px;text-align:center;}
.shares-input:focus{outline:none;border-color:var(--cyan);}
.shares-hint{font-size:.68rem;color:var(--muted);}

/* token table */
.tcard{background:var(--panel);border:1px solid var(--border2);border-radius:8px;overflow:hidden;}
.tcardh{padding:.65rem .9rem;border-bottom:1px solid var(--border);
  font-family:"Orbitron",monospace;font-size:.72rem;letter-spacing:.1em;color:var(--cyan);}
table{width:100%;border-collapse:collapse;}
th{padding:.45rem .7rem;font-size:.58rem;color:var(--muted);text-align:left;
  text-transform:uppercase;letter-spacing:.08em;border-bottom:1px solid var(--border);}
td{padding:.45rem .7rem;font-size:.8rem;border-bottom:1px solid var(--border);}
tr:last-child td{border-bottom:none;}
.btn-buy{background:rgba(0,230,118,.15);color:var(--green);
  border:1px solid rgba(0,230,118,.35);padding:.28rem .65rem;border-radius:4px;
  cursor:pointer;font-family:inherit;font-size:.72rem;transition:all .15s;}
.btn-buy:hover{background:rgba(0,230,118,.3);}
.btn-sell{background:rgba(255,23,68,.15);color:var(--red);
  border:1px solid rgba(255,23,68,.35);padding:.28rem .65rem;border-radius:4px;
  cursor:pointer;font-family:inherit;font-size:.72rem;transition:all .15s;}
.btn-sell:hover{background:rgba(255,23,68,.3);}
.btn-buy:disabled,.btn-sell:disabled{opacity:.25;cursor:not-allowed;}
.acts{display:flex;gap:.35rem;}

/* trade log */
.logcard{background:var(--panel);border:1px solid var(--border2);border-radius:8px;overflow:hidden;}
.logcardh{padding:.65rem .9rem;border-bottom:1px solid var(--border);
  font-family:"Orbitron",monospace;font-size:.72rem;letter-spacing:.1em;color:var(--cyan);}
.logbody{max-height:200px;overflow-y:auto;}
.lrow{display:flex;gap:.7rem;padding:.35rem .75rem;border-bottom:1px solid var(--border);font-size:.73rem;}
.lrow:last-child{border-bottom:none;}
.ltime{color:var(--muted);min-width:52px;flex-shrink:0;}
.lmsg{word-break:break-word;}
.lmsg.buy{color:var(--green);} .lmsg.sell{color:var(--red);} .lmsg.tp{color:var(--cyan);}
.lempty{padding:1rem;color:var(--muted);font-size:.8rem;text-align:center;}

/* toasts */
.toasts{position:fixed;bottom:1.2rem;right:1.2rem;z-index:10000;display:flex;flex-direction:column;gap:.4rem;}
.toast{padding:.55rem .9rem;border-radius:6px;font-size:.78rem;max-width:300px;
  box-shadow:0 4px 16px rgba(0,0,0,.5);animation:tin .2s ease;}
.tok{background:rgba(0,230,118,.18);border:1px solid var(--green);color:var(--green);}
.terr{background:rgba(255,23,68,.18);border:1px solid var(--red);color:var(--red);}
@keyframes tin{from{transform:translateX(110%);opacity:0;}to{transform:none;opacity:1;}}
</style>
</head>
<body>

<div class="hdr">
  <div class="logo">POLY<span>MARKET</span> — LIVE TRADING</div>
  <div class="hdr-right">
    <span class="live-dot" id="liveDot"></span><span id="liveLabel">Connecting…</span>
    <a href="/" class="back">&#8592; BOT DASHBOARD</a>
  </div>
</div>

<!-- Stats bar -->
<div class="stats">
  <div class="stat"><div class="sl">USDC Wallet</div><div class="sv c" id="sUsdc">—</div></div>
  <div class="stat"><div class="sl">Bought</div><div class="sv" id="sBought">$0.00</div></div>
  <div class="stat"><div class="sl">Sold</div><div class="sv" id="sSold">$0.00</div></div>
  <div class="stat"><div class="sl">P&amp;L</div><div class="sv" id="sPnl">$0.00</div></div>
  <div class="stat"><div class="sl">Trades</div><div class="sv y" id="sTrades">0</div></div>
  <div class="stat"><div class="sl">W / L</div><div class="sv" id="sWL">0 / 0</div></div>
  <div class="stat" style="margin-left:auto">
    <div class="sl">Bot</div>
    <div class="sv" id="sBot">—</div>
  </div>
</div>

<!-- Window bar -->
<div class="wbar">
  <span class="wlabel">WINDOW</span>
  <div class="wtrack"><div class="wfill" id="wfill" style="width:0%"></div></div>
  <span class="wtimer" id="wtimer">--:--</span>
</div>

<div class="main">

  <!-- Shares control -->
  <div class="shares-row">
    <span class="shares-label">Shares per order</span>
    <input type="number" class="shares-input" id="sharesInput" value="6" min="1" max="500">
    <span class="shares-hint">applies to all buy buttons</span>
  </div>

  <!-- Pair cards -->
  <div class="pairs">

    <!-- PAIR A -->
    <div class="pcard a">
      <div class="pcard-hdr">
        <span class="pcard-title">PAIR A &mdash; BTC&#8593; + ETH&#8595;</span>
        <span style="font-size:.6rem;color:var(--muted)">CORRELATED HEDGE</span>
      </div>
      <div class="pcard-body">
        <div class="trow">
          <span class="tname"><span class="badge btc-up">BTC&#8593;</span></span>
          <span class="tprice" id="pA_btcup" style="color:var(--btc)">—</span>
          <span class="twallet" id="wA_btcup">wallet: 0</span>
        </div>
        <div class="trow">
          <span class="tname"><span class="badge eth-dn">ETH&#8595;</span></span>
          <span class="tprice" id="pA_ethdn" style="color:var(--eth)">—</span>
          <span class="twallet" id="wA_ethdn">wallet: 0</span>
        </div>
        <div class="gapbox">
          <div class="gcol"><div class="glabel">Spread</div><div class="gvalue" id="gapA">—</div></div>
          <div class="gcol" style="text-align:right"><div class="glabel">Combined cost</div><div id="costA" style="font-size:.78rem;color:var(--muted)">—</div></div>
          <div class="gcol" style="text-align:right"><div class="glabel">Edge</div><div id="edgeA" style="font-size:.85rem">—</div></div>
        </div>
        <div class="tbar">
          <div class="tbar-labels"><span>0</span><span>0.10</span><span>0.20</span><span>0.30</span></div>
          <div class="tbar-track">
            <div class="tbar-fill" id="tbarA" style="width:0%"></div>
            <div class="tm tm1"></div><div class="tm tm2"></div><div class="tm tm3"></div>
          </div>
        </div>
        <button class="buypair" id="btnPairA" onclick="buyPair('a')">BUY PAIR A (BTC&#8593; + ETH&#8595;)</button>
      </div>
    </div>

    <!-- PAIR B -->
    <div class="pcard b">
      <div class="pcard-hdr">
        <span class="pcard-title">PAIR B &mdash; BTC&#8595; + ETH&#8593;</span>
        <span style="font-size:.6rem;color:var(--muted)">CORRELATED HEDGE</span>
      </div>
      <div class="pcard-body">
        <div class="trow">
          <span class="tname"><span class="badge btc-dn">BTC&#8595;</span></span>
          <span class="tprice" id="pB_btcdn" style="color:var(--btc)">—</span>
          <span class="twallet" id="wB_btcdn">wallet: 0</span>
        </div>
        <div class="trow">
          <span class="tname"><span class="badge eth-up">ETH&#8593;</span></span>
          <span class="tprice" id="pB_ethup" style="color:var(--eth)">—</span>
          <span class="twallet" id="wB_ethup">wallet: 0</span>
        </div>
        <div class="gapbox">
          <div class="gcol"><div class="glabel">Spread</div><div class="gvalue" id="gapB">—</div></div>
          <div class="gcol" style="text-align:right"><div class="glabel">Combined cost</div><div id="costB" style="font-size:.78rem;color:var(--muted)">—</div></div>
          <div class="gcol" style="text-align:right"><div class="glabel">Edge</div><div id="edgeB" style="font-size:.85rem">—</div></div>
        </div>
        <div class="tbar">
          <div class="tbar-labels"><span>0</span><span>0.10</span><span>0.20</span><span>0.30</span></div>
          <div class="tbar-track">
            <div class="tbar-fill" id="tbarB" style="width:0%"></div>
            <div class="tm tm1"></div><div class="tm tm2"></div><div class="tm tm3"></div>
          </div>
        </div>
        <button class="buypair" id="btnPairB" onclick="buyPair('b')">BUY PAIR B (BTC&#8595; + ETH&#8593;)</button>
      </div>
    </div>

  </div>

  <!-- Individual token table -->
  <div class="tcard">
    <div class="tcardh">INDIVIDUAL TOKENS</div>
    <table>
      <thead>
        <tr>
          <th>Token</th>
          <th>Price</th>
          <th>Wallet</th>
          <th>Cost (n shares)</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody id="tokBody">
        <tr><td colspan="5" class="lempty">Loading…</td></tr>
      </tbody>
    </table>
  </div>

  <!-- Trade log -->
  <div class="logcard">
    <div class="logcardh">TRADE LOG</div>
    <div class="logbody" id="logBody"><div class="lempty">No trades yet</div></div>
  </div>

</div>

<div class="toasts" id="toasts"></div>

<script>
var lastBal = {};

function n(v){ return parseInt(document.getElementById("sharesInput").value)||6; }
function f(v,d){ return v==null?"—":Number(v).toFixed(d!=null?d:3); }
function g(id){ return document.getElementById(id); }
function s(id,v){ var el=g(id); if(el) el.innerHTML=v; }

function toast(msg,ok){
  var c=g("toasts"), el=document.createElement("div");
  el.className="toast "+(ok?"tok":"terr");
  el.textContent=msg;
  c.appendChild(el);
  setTimeout(function(){ el.remove(); },5000);
}

function poll(){
  fetch("/api/trade/data").then(function(r){ return r.json(); }).then(function(d){
    if(!d.ok){ setLive(false,"Markets loading…"); return; }
    setLive(true,"LIVE");
    var p=d.prices||{}, tb=d.token_balances||{}, st=d.stats||{};
    lastBal=tb;

    // Stats
    s("sUsdc", d.usdc_balance!=null?"$"+f(d.usdc_balance,2):"—");
    s("sBought","$"+f(st.total_bought,2));
    s("sSold","$"+f(st.total_sold,2));
    var pnl=st.total_pnl||0;
    var pe=g("sPnl");
    if(pe){ pe.textContent=(pnl>=0?"+":"")+"$"+f(pnl,2); pe.className="sv "+(pnl>=0?"g":"r"); }
    s("sTrades",st.total_trades||0);
    s("sWL",(st.wins||0)+" / "+(st.losses||0));
    s("sBot",d.bot_running?"<span style='color:var(--green)'>RUNNING</span>":"<span style='color:var(--muted)'>STOPPED</span>");

    // Window
    var rem=d.seconds_remaining;
    if(rem!=null&&rem>0){
      var m=Math.floor(rem/60),sc=Math.floor(rem%60);
      s("wtimer",m+":"+(sc<10?"0":"")+sc);
      g("wfill").style.width=Math.min(100,(rem/300)*100)+"%";
    } else {
      s("wtimer","--:--"); g("wfill").style.width="0%";
    }

    // Pair A: btc_up + eth_down
    var pA1=p.btc_up, pA2=p.eth_down;
    s("pA_btcup",pA1!=null?f(pA1):"—");
    s("pA_ethdn",pA2!=null?f(pA2):"—");
    setWallet("wA_btcup",tb.btc_up);
    setWallet("wA_ethdn",tb.eth_down);
    if(pA1!=null&&pA2!=null){
      var gA=Math.abs(pA1-pA2), cA=pA1+pA2, eA=((1-cA)*100);
      s("gapA",f(gA,3));
      s("costA","$"+f(cA,3)+"/share");
      s("edgeA","<span style='color:"+(eA>0?"var(--green)":"var(--red)")+"'>"+(eA>0?"+":"")+f(eA,1)+"%</span>");
      g("tbarA").style.width=Math.min(100,(gA/0.30)*100)+"%";
    }

    // Pair B: btc_down + eth_up
    var pB1=p.btc_down, pB2=p.eth_up;
    s("pB_btcdn",pB1!=null?f(pB1):"—");
    s("pB_ethup",pB2!=null?f(pB2):"—");
    setWallet("wB_btcdn",tb.btc_down);
    setWallet("wB_ethup",tb.eth_up);
    if(pB1!=null&&pB2!=null){
      var gB=Math.abs(pB1-pB2), cB=pB1+pB2, eB=((1-cB)*100);
      s("gapB",f(gB,3));
      s("costB","$"+f(cB,3)+"/share");
      s("edgeB","<span style='color:"+(eB>0?"var(--green)":"var(--red)")+"'>"+(eB>0?"+":"")+f(eB,1)+"%</span>");
      g("tbarB").style.width=Math.min(100,(gB/0.30)*100)+"%";
    }

    // Token table
    var TOKS=[
      {key:"btc_up",  label:"BTC&#8593;", cls:"btc-up", p:pA1},
      {key:"btc_down",label:"BTC&#8595;", cls:"btc-dn", p:pB1},
      {key:"eth_up",  label:"ETH&#8593;", cls:"eth-up", p:pB2},
      {key:"eth_down",label:"ETH&#8595;", cls:"eth-dn", p:pA2},
    ];
    var shares=n(), html="";
    for(var i=0;i<TOKS.length;i++){
      var t=TOKS[i];
      var bal=tb[t.key]||0, hasBal=bal>0.001;
      var cost=t.p!=null?"$"+f(t.p*shares,2):"—";
      html+="<tr>"+
        "<td><span class='badge "+t.cls+"'>"+t.label+"</span></td>"+
        "<td style='font-weight:700'>"+f(t.p)+"</td>"+
        "<td class='"+(hasBal?"twallet has":"twallet")+"'>"+(hasBal?f(bal,4):"0")+"</td>"+
        "<td>"+cost+"</td>"+
        "<td class='acts'>"+
          "<button class='btn-buy' onclick='buyToken(""+t.key+"")'>BUY</button>"+
          "<button class='btn-sell' onclick='sellToken(""+t.key+"")' "+(hasBal?"":"disabled")+">SELL</button>"+
        "</td>"+
      "</tr>";
    }
    g("tokBody").innerHTML=html;

    // Trade log
    var logs=d.trade_log||[];
    if(!logs.length){ g("logBody").innerHTML='<div class="lempty">No trades yet</div>'; }
    else {
      var lh="";
      for(var j=0;j<Math.min(logs.length,25);j++){
        var e=logs[j], msg=e.msg||"";
        var mc=msg.indexOf("BUY")>=0?"buy":msg.indexOf("SELL")>=0?"sell":msg.indexOf("TP")>=0?"tp":"";
        lh+='<div class="lrow"><span class="ltime">'+e.time+'</span><span class="lmsg '+mc+'">'+msg+'</span></div>';
      }
      g("logBody").innerHTML=lh;
    }
  }).catch(function(){ setLive(false,"Error"); });
}

function setLive(on,label){
  g("liveDot").className="live-dot"+(on?" on":"");
  s("liveLabel",label);
}

function setWallet(id,val){
  var el=g(id); if(!el) return;
  var v=val||0;
  el.textContent="wallet: "+(v>0.001?f(v,4):"0");
  el.className="twallet"+(v>0.001?" has":"");
}

async function buyPair(pair){
  var btn=g(pair==="a"?"btnPairA":"btnPairB");
  if(btn) btn.disabled=true;
  try{
    var r=await fetch("/api/manual/buy_pair",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({pair:pair,shares:n()})});
    var d=await r.json();
    if(d.ok) toast("Pair "+pair.toUpperCase()+" bought. TP placed at 0.985",true);
    else toast("Failed: "+(d.msg||"see log"),false);
    poll();
  }catch(e){ toast("Request error: "+e.message,false); }
  finally{ if(btn) btn.disabled=false; }
}

async function buyToken(key){
  try{
    var r=await fetch("/api/manual/buy_token",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({key:key,shares:n()})});
    var d=await r.json();
    if(d.ok) toast("Bought "+n()+"x "+key+" @ "+f(d.price)+". TP placed.",true);
    else toast("Buy failed: "+(d.msg||d.error||"see log"),false);
    poll();
  }catch(e){ toast("Request error: "+e.message,false); }
}

async function sellToken(key){
  var bal=lastBal[key]||0;
  if(bal<0.001){ toast("No balance to sell",false); return; }
  if(!confirm("Sell "+f(bal,4)+" shares of "+key+"?")) return;
  try{
    var r=await fetch("/api/manual/sell_token",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({key:key,shares:0})});
    var d=await r.json();
    if(d.ok) toast("Sell order placed: "+f(d.shares,4)+"x "+key+" @ "+f(d.price),true);
    else toast("Sell failed: "+(d.msg||d.error||"see log"),false);
    poll();
  }catch(e){ toast("Request error: "+e.message,false); }
}

setInterval(poll,1000);
poll();
</script>
</body>
</html>
"""