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

    <!-- Spread UP -->
    <div class="panel cyan">
      <div class="panel-label">Spread — UP Markets (BTC vs ETH)</div>
      <div class="spread-val" id="spreadUp">0.000</div>
      <div class="spread-bar-wrap">
        <div class="spread-bar-bg"><div class="spread-bar-fill" id="spreadUpBar" style="width:0%"></div></div>
        <div class="spread-threshold"><span>0.00</span><span>ENTRY: 0.15</span><span>0.30</span></div>
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

    <!-- Spread DOWN -->
    <div class="panel orange">
      <div class="panel-label">Spread — DOWN Markets (BTC vs ETH)</div>
      <div class="spread-val" style="color:var(--orange)" id="spreadDown">0.000</div>
      <div class="spread-bar-wrap">
        <div class="spread-bar-bg"><div class="spread-bar-fill" id="spreadDownBar" style="width:0%;background:linear-gradient(90deg,var(--orange),var(--yellow))"></div></div>
        <div class="spread-threshold"><span>0.00</span><span>ENTRY: 0.15</span><span>0.30</span></div>
      </div>
    </div>

  </div>

  <!-- Positions Row -->
  <div class="mid-row">
    <div class="panel yellow">
      <div class="panel-label">Position — UP Markets</div>
      <div id="posUp"><div class="pos-empty">No position open</div></div>
    </div>
    <div class="panel">
      <div class="panel-label">Last Signal</div>
      <div id="lastSignal" style="font-size:0.7rem;color:var(--muted);margin-top:0.3rem">—</div>
    </div>
    <div class="panel yellow">
      <div class="panel-label">Position — DOWN Markets</div>
      <div id="posDown"><div class="pos-empty">No position open</div></div>
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

function setSpread(dir, val) {
  let idVal = dir === 'up' ? 'spreadUp' : 'spreadDown';
  let idBar = dir === 'up' ? 'spreadUpBar' : 'spreadDownBar';
  let el = document.getElementById(idVal);
  let bar = document.getElementById(idBar);
  if (!el || !bar) return;
  if (val == null) { el.textContent = '0.000'; bar.style.width = '0%'; return; }
  el.textContent = parseFloat(val).toFixed(3);
  let pct = Math.min(100, (val / 0.30) * 100);
  bar.style.width = pct + '%';
  bar.className = 'spread-bar-fill' + (val >= 0.15 ? ' triggered' : '');
}

function renderPos(dir, pos) {
  let el = document.getElementById('pos' + (dir === 'up' ? 'Up' : 'Down'));
  if (!el) return;
  if (!pos) { el.innerHTML = '<div class="pos-empty">No position open</div>'; return; }

  let now = Date.now() / 1000;
  let dur = pos.entry_time ? Math.floor(now - pos.entry_time) : 0;

  let chainMatch = pos.real_shares === pos.shares;
  let realCol    = chainMatch ? 'var(--green)' : 'var(--yellow)';
  el.innerHTML = `
    <div class="pos-side" style="color:var(--yellow)">${pos.price_key.toUpperCase()}</div>
    <div class="pos-row"><span class="label">Tracked Shares</span><span>${pos.shares}</span></div>
    <div class="pos-row"><span class="label">Chain Balance</span><span style="color:${realCol}">${pos.real_shares}</span></div>
    <div class="pos-row"><span class="label">Entry Cost</span><span>$${parseFloat(pos.entry_cost).toFixed(4)}</span></div>
    <div class="pos-row"><span class="label">Entry Price</span><span>${parseFloat(pos.entry_price).toFixed(4)}</span></div>
    <div class="pos-row"><span class="label">Entry Spread</span><span>${parseFloat(pos.entry_spread).toFixed(4)}</span></div>
    <div class="pos-row"><span class="label">Duration</span><span>${dur}s</span></div>
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

    // Status dot
    let dot = document.getElementById('statusDot');
    let txt = document.getElementById('statusText');
    if (d.running) {
      dot.className = d.force_closing ? 'dot warn' : 'dot live';
      txt.textContent = d.force_closing ? 'FORCE CLOSE' : 'LIVE';
    } else {
      dot.className = 'dot idle'; txt.textContent = 'IDLE';
    }

    document.getElementById('forceBanner').className = 'force-banner' + (d.force_closing ? ' visible' : '');

    // DRY RUN badge (fetch from /api/health first tick)
    if (d.prices) {
      ['btc_up','btc_down','eth_up','eth_down'].forEach(k => setPrice(k, d.prices[k]));
      prevPrices = { ...d.prices };
    }

    setSpread('up',   d.spreads?.up);
    setSpread('down', d.spreads?.down);
    renderTimer(d.seconds_remaining);
    renderPos('up',   d.positions?.up);
    renderPos('down', d.positions?.down);

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
    if (d.spreads?.up != null && d.spreads?.down != null) {
      let su = parseFloat(d.spreads.up || 0);
      let sd = parseFloat(d.spreads.down || 0);
      let sig = su >= 0.15 ? `UP spread triggered (${su.toFixed(3)})` : sd >= 0.15 ? `DOWN spread triggered (${sd.toFixed(3)})` : 'Watching…';
      document.getElementById('lastSignal').textContent = sig;
      document.getElementById('lastSignal').style.color = (su >= 0.15 || sd >= 0.15) ? 'var(--green)' : 'var(--muted)';
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
