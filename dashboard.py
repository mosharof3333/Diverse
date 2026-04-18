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
<title>Manual Trading</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#060810;--panel:#0b0d14;--border:#151928;--border2:#1e2235;
  --green:#00e676;--red:#ff1744;--blue:#2979ff;--yellow:#ffea00;
  --orange:#ff6d00;--cyan:#00e5ff;--text:#cdd6f4;--muted:#45475a;
  --btc:#f7931a;--eth:#627eea;
}
*{margin:0;padding:0;box-sizing:border-box;}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:'Share Tech Mono',monospace;overflow-x:hidden;}
body::before{content:'';position:fixed;top:0;left:0;right:0;bottom:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.03) 2px,rgba(0,0,0,0.03) 4px);
  pointer-events:none;z-index:9999;}

.header{display:flex;align-items:center;justify-content:space-between;
  padding:1rem 1.5rem;border-bottom:1px solid var(--border2);
  background:linear-gradient(90deg,#060810,#0b0d18,#060810);
  position:sticky;top:0;z-index:100;}
.logo{font-family:'Orbitron',monospace;font-weight:900;font-size:1.1rem;
  color:var(--cyan);letter-spacing:0.15em;text-shadow:0 0 20px rgba(0,229,255,0.5);}
.logo span{color:var(--muted);}
.header-right{display:flex;align-items:center;gap:0.8rem;}
.back-btn{background:transparent;border:1px solid var(--border2);color:var(--muted);
  padding:0.4rem 0.9rem;border-radius:4px;cursor:pointer;font-family:inherit;font-size:0.75rem;
  text-decoration:none;display:inline-block;transition:all 0.2s;}
.back-btn:hover{border-color:var(--cyan);color:var(--cyan);}

/* Stats bar */
.stats-bar{display:flex;gap:1rem;flex-wrap:wrap;padding:0.75rem 1.5rem;
  background:var(--panel);border-bottom:1px solid var(--border);}
.stat{display:flex;flex-direction:column;gap:0.1rem;}
.stat-label{font-size:0.6rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.1em;}
.stat-value{font-size:0.95rem;font-weight:700;}
.stat-value.green{color:var(--green);}
.stat-value.red{color:var(--red);}
.stat-value.cyan{color:var(--cyan);}
.stat-value.yellow{color:var(--yellow);}
.stat-value.muted{color:var(--muted);}

/* Window countdown */
.window-bar{display:flex;align-items:center;justify-content:space-between;
  padding:0.5rem 1.5rem;background:#080a10;border-bottom:1px solid var(--border);}
.window-info{font-size:0.8rem;color:var(--muted);}
.window-timer{font-family:'Orbitron',monospace;font-size:1.1rem;color:var(--yellow);
  text-shadow:0 0 10px rgba(255,234,0,0.4);}
.window-progress{flex:1;margin:0 1rem;height:4px;background:var(--border);border-radius:2px;overflow:hidden;}
.window-progress-fill{height:100%;background:linear-gradient(90deg,var(--green),var(--yellow));
  transition:width 0.5s linear;border-radius:2px;}

/* Main grid */
.main{padding:1.5rem;display:grid;gap:1rem;}
.pairs-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;}
@media(max-width:800px){.pairs-grid{grid-template-columns:1fr;}}

/* Pair card */
.pair-card{background:var(--panel);border:1px solid var(--border2);border-radius:8px;overflow:hidden;}
.pair-card.pair-a{border-top:2px solid var(--btc);}
.pair-card.pair-b{border-top:2px solid var(--eth);}
.pair-header{padding:0.75rem 1rem;display:flex;align-items:center;justify-content:space-between;
  border-bottom:1px solid var(--border);}
.pair-title{font-family:'Orbitron',monospace;font-size:0.8rem;letter-spacing:0.1em;}
.pair-a .pair-title{color:var(--btc);}
.pair-b .pair-title{color:var(--eth);}
.pair-body{padding:1rem;}

.token-row{display:flex;align-items:center;justify-content:space-between;
  padding:0.5rem 0;border-bottom:1px solid var(--border);}
.token-row:last-child{border-bottom:none;}
.token-name{font-size:0.8rem;min-width:90px;}
.token-price{font-size:1.1rem;font-weight:700;min-width:70px;text-align:right;}
.token-wallet{font-size:0.75rem;color:var(--muted);min-width:80px;text-align:right;}

.gap-display{display:flex;align-items:center;justify-content:space-between;
  margin:0.75rem 0;padding:0.6rem 0.75rem;
  background:#0d0f18;border-radius:6px;border:1px solid var(--border);}
.gap-label{font-size:0.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;}
.gap-value{font-size:1.3rem;font-family:'Orbitron',monospace;font-weight:700;}
.gap-edge{font-size:0.75rem;color:var(--muted);}
.gap-edge.positive{color:var(--green);}

.threshold-bar{margin:0.5rem 0 0.75rem;}
.threshold-labels{display:flex;justify-content:space-between;font-size:0.6rem;color:var(--muted);margin-bottom:0.25rem;}
.threshold-track{height:6px;background:var(--border);border-radius:3px;position:relative;overflow:visible;}
.threshold-fill{height:100%;border-radius:3px;transition:width 0.3s ease;background:linear-gradient(90deg,var(--green),var(--yellow),var(--red));}
.threshold-marker{position:absolute;top:-4px;width:2px;height:14px;border-radius:1px;}
.threshold-marker.t1{background:var(--green);}
.threshold-marker.t2{background:var(--yellow);}
.threshold-marker.t3{background:var(--red);}

.buy-pair-btn{width:100%;padding:0.7rem;font-family:'Orbitron',monospace;font-size:0.85rem;
  font-weight:700;letter-spacing:0.1em;border:none;border-radius:6px;cursor:pointer;
  transition:all 0.15s;margin-top:0.5rem;}
.pair-a .buy-pair-btn{background:linear-gradient(135deg,var(--btc),#e07b10);color:#000;}
.pair-b .buy-pair-btn{background:linear-gradient(135deg,var(--eth),#4a5fc0);color:#fff;}
.buy-pair-btn:hover{transform:translateY(-1px);box-shadow:0 4px 20px rgba(0,0,0,0.4);}
.buy-pair-btn:active{transform:translateY(0);}
.buy-pair-btn:disabled{opacity:0.4;cursor:not-allowed;transform:none;}

/* Token table */
.token-table-card{background:var(--panel);border:1px solid var(--border2);border-radius:8px;overflow:hidden;}
.card-header{padding:0.75rem 1rem;border-bottom:1px solid var(--border);
  font-family:'Orbitron',monospace;font-size:0.75rem;letter-spacing:0.1em;color:var(--cyan);}
table{width:100%;border-collapse:collapse;}
th{padding:0.5rem 0.75rem;font-size:0.6rem;color:var(--muted);text-align:left;
  text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid var(--border);}
td{padding:0.5rem 0.75rem;font-size:0.8rem;border-bottom:1px solid var(--border);}
tr:last-child td{border-bottom:none;}
tr:hover td{background:rgba(255,255,255,0.02);}

.token-badge{display:inline-block;padding:0.15rem 0.5rem;border-radius:3px;
  font-size:0.7rem;font-weight:700;margin-right:0.25rem;}
.badge-btc{background:rgba(247,147,26,0.15);color:var(--btc);border:1px solid rgba(247,147,26,0.3);}
.badge-eth{background:rgba(98,126,234,0.15);color:var(--eth);border:1px solid rgba(98,126,234,0.3);}
.badge-up{background:rgba(0,230,118,0.1);color:var(--green);border:1px solid rgba(0,230,118,0.2);}
.badge-down{background:rgba(255,23,68,0.1);color:var(--red);border:1px solid rgba(255,23,68,0.2);}

.price-cell{font-size:0.9rem;font-weight:700;}
.wallet-cell{color:var(--cyan);}
.wallet-cell.has-balance{color:var(--yellow);font-weight:700;}
.action-btns{display:flex;gap:0.4rem;}
.btn-buy{background:rgba(0,230,118,0.15);color:var(--green);border:1px solid rgba(0,230,118,0.3);
  padding:0.3rem 0.7rem;border-radius:4px;cursor:pointer;font-family:inherit;font-size:0.75rem;
  transition:all 0.15s;}
.btn-buy:hover{background:rgba(0,230,118,0.3);}
.btn-sell{background:rgba(255,23,68,0.15);color:var(--red);border:1px solid rgba(255,23,68,0.3);
  padding:0.3rem 0.7rem;border-radius:4px;cursor:pointer;font-family:inherit;font-size:0.75rem;
  transition:all 0.15s;}
.btn-sell:hover{background:rgba(255,23,68,0.3);}
.btn-buy:disabled,.btn-sell:disabled{opacity:0.3;cursor:not-allowed;}

/* Shares control */
.shares-control{display:flex;align-items:center;gap:0.75rem;padding:0.75rem 1rem;
  background:var(--panel);border:1px solid var(--border2);border-radius:8px;}
.shares-label{font-size:0.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;}
.shares-input{background:#0d0f18;border:1px solid var(--border2);color:var(--text);
  padding:0.4rem 0.6rem;border-radius:4px;font-family:inherit;font-size:1rem;
  width:80px;text-align:center;}
.shares-input:focus{outline:none;border-color:var(--cyan);}

/* Trade log */
.log-card{background:var(--panel);border:1px solid var(--border2);border-radius:8px;overflow:hidden;}
.log-body{max-height:220px;overflow-y:auto;padding:0;}
.log-entry{display:flex;gap:0.75rem;padding:0.4rem 0.75rem;border-bottom:1px solid var(--border);font-size:0.75rem;}
.log-entry:last-child{border-bottom:none;}
.log-time{color:var(--muted);min-width:55px;}
.log-msg{color:var(--text);}
.log-msg.buy{color:var(--green);}
.log-msg.sell{color:var(--red);}
.log-msg.tp{color:var(--cyan);}
.log-msg.err{color:var(--orange);}
.log-empty{padding:1rem;color:var(--muted);font-size:0.8rem;text-align:center;}

/* Toast */
.toast-container{position:fixed;bottom:1.5rem;right:1.5rem;z-index:10000;display:flex;flex-direction:column;gap:0.5rem;}
.toast{padding:0.6rem 1rem;border-radius:6px;font-size:0.8rem;animation:slideIn 0.2s ease;
  box-shadow:0 4px 20px rgba(0,0,0,0.5);max-width:320px;}
.toast.ok{background:rgba(0,230,118,0.2);border:1px solid var(--green);color:var(--green);}
.toast.err{background:rgba(255,23,68,0.2);border:1px solid var(--red);color:var(--red);}
@keyframes slideIn{from{transform:translateX(100%);opacity:0;}to{transform:translateX(0);opacity:1;}}

.status-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:0.4rem;}
.status-dot.live{background:var(--green);box-shadow:0 0 6px var(--green);animation:pulse 1.5s infinite;}
.status-dot.offline{background:var(--red);}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.4;}}

.no-market{color:var(--muted);font-size:0.75rem;padding:0.5rem 0;}
</style>
</head>
<body>

<div class="header">
  <div class="logo">POLY<span>MARKET</span> — MANUAL TRADING</div>
  <div class="header-right">
    <a href="/" class="back-btn">← BOT DASHBOARD</a>
  </div>
</div>

<!-- Stats bar -->
<div class="stats-bar">
  <div class="stat">
    <div class="stat-label">USDC Wallet</div>
    <div class="stat-value cyan" id="sUsdc">—</div>
  </div>
  <div class="stat">
    <div class="stat-label">Total Bought</div>
    <div class="stat-value" id="sBought">$0.00</div>
  </div>
  <div class="stat">
    <div class="stat-label">Total Sold</div>
    <div class="stat-value" id="sSold">$0.00</div>
  </div>
  <div class="stat">
    <div class="stat-label">Bot PnL</div>
    <div class="stat-value" id="sPnl">$0.00</div>
  </div>
  <div class="stat">
    <div class="stat-label">Trades</div>
    <div class="stat-value yellow" id="sTrades">0</div>
  </div>
  <div class="stat">
    <div class="stat-label">W / L</div>
    <div class="stat-value" id="sWL">0 / 0</div>
  </div>
  <div class="stat" style="margin-left:auto;">
    <div class="stat-label">Bot Status</div>
    <div class="stat-value" id="sBotStatus"><span class="status-dot offline" id="statusDot"></span><span id="statusTxt">Checking…</span></div>
  </div>
</div>

<!-- Window bar -->
<div class="window-bar">
  <div class="window-info">5-MIN WINDOW</div>
  <div class="window-progress"><div class="window-progress-fill" id="wProgress" style="width:0%"></div></div>
  <div class="window-timer" id="wTimer">--:--</div>
</div>

<div class="main">

  <!-- Shares control -->
  <div class="shares-control">
    <span class="shares-label">Shares per order:</span>
    <input type="number" class="shares-input" id="sharesInput" value="6" min="1" max="100">
    <span style="font-size:0.75rem;color:var(--muted);">— applies to all BUY buttons below</span>
  </div>

  <!-- Pair cards -->
  <div class="pairs-grid">

    <!-- PAIR A: BTC↑ + ETH↓ -->
    <div class="pair-card pair-a" id="pairACard">
      <div class="pair-header">
        <span class="pair-title">PAIR A — BTC&#8593; + ETH&#8595;</span>
        <span style="font-size:0.65rem;color:var(--muted);">CORRELATED HEDGE</span>
      </div>
      <div class="pair-body">
        <div class="token-row">
          <span class="token-name"><span class="token-badge badge-btc badge-up">BTC&#8593;</span></span>
          <span class="token-price" id="pA1" style="color:var(--btc)">—</span>
          <span class="token-wallet" id="wA1">wallet: —</span>
        </div>
        <div class="token-row">
          <span class="token-name"><span class="token-badge badge-eth badge-down">ETH&#8595;</span></span>
          <span class="token-price" id="pA2" style="color:var(--eth)">—</span>
          <span class="token-wallet" id="wA2">wallet: —</span>
        </div>
        <div class="gap-display">
          <div>
            <div class="gap-label">Spread (Gap)</div>
            <div class="gap-value" id="gapA" style="color:var(--yellow)">—</div>
          </div>
          <div style="text-align:right;">
            <div class="gap-label">Cost to buy both</div>
            <div class="gap-edge" id="costA">—</div>
          </div>
          <div style="text-align:right;">
            <div class="gap-label">Edge if one wins</div>
            <div class="gap-edge" id="edgeA">—</div>
          </div>
        </div>
        <div class="threshold-bar">
          <div class="threshold-labels">
            <span>0</span><span>0.10</span><span>0.20</span><span>0.30+</span>
          </div>
          <div class="threshold-track">
            <div class="threshold-fill" id="tFillA" style="width:0%"></div>
            <div class="threshold-marker t1" style="left:33.3%"></div>
            <div class="threshold-marker t2" style="left:50%"></div>
            <div class="threshold-marker t3" style="left:100%"></div>
          </div>
        </div>
        <button class="buy-pair-btn" id="buyPairABtn" onclick="buyPair('a')">
          BUY PAIR A (BTC&#8593; + ETH&#8595;)
        </button>
      </div>
    </div>

    <!-- PAIR B: BTC↓ + ETH↑ -->
    <div class="pair-card pair-b" id="pairBCard">
      <div class="pair-header">
        <span class="pair-title">PAIR B — BTC&#8595; + ETH&#8593;</span>
        <span style="font-size:0.65rem;color:var(--muted);">CORRELATED HEDGE</span>
      </div>
      <div class="pair-body">
        <div class="token-row">
          <span class="token-name"><span class="token-badge badge-btc badge-down">BTC&#8595;</span></span>
          <span class="token-price" id="pB1" style="color:var(--btc)">—</span>
          <span class="token-wallet" id="wB1">wallet: —</span>
        </div>
        <div class="token-row">
          <span class="token-name"><span class="token-badge badge-eth badge-up">ETH&#8593;</span></span>
          <span class="token-price" id="pB2" style="color:var(--eth)">—</span>
          <span class="token-wallet" id="wB2">wallet: —</span>
        </div>
        <div class="gap-display">
          <div>
            <div class="gap-label">Spread (Gap)</div>
            <div class="gap-value" id="gapB" style="color:var(--yellow)">—</div>
          </div>
          <div style="text-align:right;">
            <div class="gap-label">Cost to buy both</div>
            <div class="gap-edge" id="costB">—</div>
          </div>
          <div style="text-align:right;">
            <div class="gap-label">Edge if one wins</div>
            <div class="gap-edge" id="edgeB">—</div>
          </div>
        </div>
        <div class="threshold-bar">
          <div class="threshold-labels">
            <span>0</span><span>0.10</span><span>0.20</span><span>0.30+</span>
          </div>
          <div class="threshold-track">
            <div class="threshold-fill" id="tFillB" style="width:0%"></div>
            <div class="threshold-marker t1" style="left:33.3%"></div>
            <div class="threshold-marker t2" style="left:50%"></div>
            <div class="threshold-marker t3" style="left:100%"></div>
          </div>
        </div>
        <button class="buy-pair-btn" id="buyPairBBtn" onclick="buyPair('b')">
          BUY PAIR B (BTC&#8595; + ETH&#8593;)
        </button>
      </div>
    </div>

  </div>

  <!-- Individual token table -->
  <div class="token-table-card">
    <div class="card-header">INDIVIDUAL TOKENS — BUY / SELL</div>
    <table>
      <thead>
        <tr>
          <th>Token</th>
          <th>Live Price</th>
          <th>Wallet Balance</th>
          <th>Est. Cost (n shares)</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody id="tokenTbody">
        <tr><td colspan="5" class="log-empty">Waiting for market data…</td></tr>
      </tbody>
    </table>
  </div>

  <!-- Trade log -->
  <div class="log-card">
    <div class="card-header">TRADE LOG</div>
    <div class="log-body" id="tradeLog">
      <div class="log-empty">No trades yet</div>
    </div>
  </div>

</div><!-- /main -->

<div class="toast-container" id="toastContainer"></div>

<script>
const TOKENS = [
  { key:'btc_up',   label:'BTC&#8593;', assetClass:'badge-btc', dirClass:'badge-up'   },
  { key:'btc_down', label:'BTC&#8595;', assetClass:'badge-btc', dirClass:'badge-down' },
  { key:'eth_up',   label:'ETH&#8593;', assetClass:'badge-eth', dirClass:'badge-up'   },
  { key:'eth_down', label:'ETH&#8595;', assetClass:'badge-eth', dirClass:'badge-down' },
];

let lastData = null;

function shares() {
  return parseInt(document.getElementById('sharesInput').value) || 6;
}

function toast(msg, ok=true) {
  const c = document.getElementById('toastContainer');
  const el = document.createElement('div');
  el.className = 'toast ' + (ok ? 'ok' : 'err');
  el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function fmt(v, decimals=3) {
  if (v == null) return '—';
  return Number(v).toFixed(decimals);
}

function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = val;
}

function poll() {
  fetch('/api/state').then(r => r.json()).then(d => {
    lastData = d;
    updateUI(d);
  }).catch(() => {});
}

function updateUI(d) {
  const p = d.prices || {};
  const s = d.stats  || {};
  const tb = d.token_balances || {};

  // Stats bar
  const usdc = d.usdc_balance != null ? '$' + fmt(d.usdc_balance, 2) : '—';
  setEl('sUsdc', usdc);
  setEl('sBought',  '$' + fmt(s.total_bought, 2));
  setEl('sSold',    '$' + fmt(s.total_sold,   2));
  const pnl = (s.total_pnl || 0);
  const pnlEl = document.getElementById('sPnl');
  if (pnlEl) {
    pnlEl.textContent = (pnl >= 0 ? '+' : '') + '$' + fmt(pnl, 2);
    pnlEl.className = 'stat-value ' + (pnl >= 0 ? 'green' : 'red');
  }
  setEl('sTrades', s.total_trades || 0);
  setEl('sWL', (s.wins||0) + ' / ' + (s.losses||0));

  // Bot status
  const dot = document.getElementById('statusDot');
  const txt = document.getElementById('statusTxt');
  if (dot && txt) {
    if (d.running) { dot.className='status-dot live'; txt.textContent='RUNNING'; }
    else           { dot.className='status-dot offline'; txt.textContent='STOPPED'; }
  }

  // Window timer
  const rem = d.seconds_remaining;
  if (rem != null && rem > 0) {
    const m = Math.floor(rem / 60), s2 = Math.floor(rem % 60);
    setEl('wTimer', m + ':' + String(s2).padStart(2,'0'));
    const pct = Math.max(0, Math.min(100, (rem / 300) * 100));
    const fill = document.getElementById('wProgress');
    if (fill) fill.style.width = pct + '%';
  } else {
    setEl('wTimer', '--:--');
  }

  // Pair A: btc_up + eth_down
  const pA1 = p.btc_up,  pA2 = p.eth_down;
  const pB1 = p.btc_down, pB2 = p.eth_up;
  setEl('pA1', pA1 != null ? fmt(pA1) : '—');
  setEl('pA2', pA2 != null ? fmt(pA2) : '—');
  setEl('wA1', 'wallet: ' + fmt(tb.btc_up  || 0, 4));
  setEl('wA2', 'wallet: ' + fmt(tb.eth_down|| 0, 4));
  setEl('pB1', pB1 != null ? fmt(pB1) : '—');
  setEl('pB2', pB2 != null ? fmt(pB2) : '—');
  setEl('wB1', 'wallet: ' + fmt(tb.btc_down|| 0, 4));
  setEl('wB2', 'wallet: ' + fmt(tb.eth_up  || 0, 4));

  // Gaps
  if (pA1 != null && pA2 != null) {
    const gA  = Math.abs(pA1 - pA2);
    const cA  = pA1 + pA2;
    const eA  = ((1.0 - cA) * 100).toFixed(1);
    setEl('gapA',  fmt(gA, 3));
    setEl('costA', '$' + fmt(cA, 3) + ' per share');
    const edgeEl = document.getElementById('edgeA');
    if (edgeEl) {
      edgeEl.textContent = eA + '% edge';
      edgeEl.className = 'gap-edge ' + (parseFloat(eA) > 0 ? 'positive' : '');
    }
    const pct = Math.min(100, (gA / 0.30) * 100);
    const fill = document.getElementById('tFillA');
    if (fill) fill.style.width = pct + '%';
  }
  if (pB1 != null && pB2 != null) {
    const gB  = Math.abs(pB1 - pB2);
    const cB  = pB1 + pB2;
    const eB  = ((1.0 - cB) * 100).toFixed(1);
    setEl('gapB',  fmt(gB, 3));
    setEl('costB', '$' + fmt(cB, 3) + ' per share');
    const edgeEl = document.getElementById('edgeB');
    if (edgeEl) {
      edgeEl.textContent = eB + '% edge';
      edgeEl.className = 'gap-edge ' + (parseFloat(eB) > 0 ? 'positive' : '');
    }
    const pct = Math.min(100, (gB / 0.30) * 100);
    const fill = document.getElementById('tFillB');
    if (fill) fill.style.width = pct + '%';
  }

  // Token table
  const mf = d.markets_found || {};
  const tbody = document.getElementById('tokenTbody');
  if (tbody) {
    let html = '';
    for (const t of TOKENS) {
      const price = p[t.key];
      const bal   = tb[t.key] || 0;
      const cost  = price != null ? '$' + fmt(price * shares(), 2) : '—';
      const priceStr = price != null ? fmt(price) : '—';
      const balStr   = fmt(bal, 4);
      const hasBal   = bal > 0.001;
      const hasMarket = mf[t.key];
      html += `<tr>
        <td><span class="token-badge ${t.assetClass} ${t.dirClass}">${t.label}</span></td>
        <td class="price-cell">${priceStr}</td>
        <td class="wallet-cell ${hasBal?'has-balance':''}">${balStr}</td>
        <td>${cost}</td>
        <td class="action-btns">
          <button class="btn-buy" onclick="buyToken('${t.key}')" ${!hasMarket?'disabled':''}>BUY</button>
          <button class="btn-sell" onclick="sellToken('${t.key}')" ${!hasBal?'disabled':''}>SELL ALL</button>
        </td>
      </tr>`;
    }
    tbody.innerHTML = html || '<tr><td colspan="5" class="log-empty">No market data</td></tr>';
  }

  // Trade log
  const logs = d.trade_log || [];
  const logEl = document.getElementById('tradeLog');
  if (logEl) {
    if (!logs.length) {
      logEl.innerHTML = '<div class="log-empty">No trades yet</div>';
    } else {
      let html = '';
      for (const e of logs.slice(0, 30)) {
        const msg = e.msg || '';
        let cls = '';
        if (msg.includes('BUY'))  cls = 'buy';
        if (msg.includes('SELL')) cls = 'sell';
        if (msg.includes('TP'))   cls = 'tp';
        if (msg.includes('ERR') || msg.includes('fail')) cls = 'err';
        html += `<div class="log-entry"><span class="log-time">${e.time}</span><span class="log-msg ${cls}">${msg}</span></div>`;
      }
      logEl.innerHTML = html;
    }
  }
}

async function buyPair(pair) {
  const btn = document.getElementById(pair === 'a' ? 'buyPairABtn' : 'buyPairBBtn');
  if (btn) btn.disabled = true;
  try {
    const resp = await fetch('/api/manual/buy_pair', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ pair, shares: shares() })
    });
    const data = await resp.json();
    if (data.ok) {
      toast('Pair ' + pair.toUpperCase() + ' bought — TP placed at 0.985', true);
    } else {
      toast('Buy pair failed: ' + (data.msg || JSON.stringify(data.results)), false);
    }
    poll();
  } catch(e) {
    toast('Request failed: ' + e.message, false);
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function buyToken(key) {
  try {
    const resp = await fetch('/api/manual/buy_token', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ key, shares: shares() })
    });
    const data = await resp.json();
    if (data.ok) toast('Bought ' + shares() + 'x ' + key + ' — TP placed', true);
    else toast('Buy failed: ' + (data.msg || data.error), false);
    poll();
  } catch(e) {
    toast('Request failed: ' + e.message, false);
  }
}

async function sellToken(key) {
  const bal = lastData && lastData.token_balances ? lastData.token_balances[key] : 0;
  if (!bal || bal < 0.001) { toast('No balance to sell', false); return; }
  if (!confirm('Sell all ' + bal.toFixed(4) + ' shares of ' + key + '?')) return;
  try {
    const resp = await fetch('/api/manual/sell_token', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ key, shares: 0 })  // 0 = use full wallet balance
    });
    const data = await resp.json();
    if (data.ok) toast('Sold ' + key + ' — order placed', true);
    else toast('Sell failed: ' + (data.msg || data.error), false);
    poll();
  } catch(e) {
    toast('Request failed: ' + e.message, false);
  }
}

setInterval(poll, 800);
poll();
</script>
</body>
</html>
"""
