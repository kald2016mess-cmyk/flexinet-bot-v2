export function buildMiniappHtml(opts: { adsgramBlockId?: string } = {}): string {
  const blockId = (opts.adsgramBlockId || "").replace(/[^a-zA-Z0-9_-]/g, "");
  return MINIAPP_HTML.replace("__ADSGRAM_BLOCK_ID__", blockId);
}

export const MINIAPP_HTML = `<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
<title>شبكتي</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<script src="https://sad.adsgram.ai/js/sad.min.js"></script>
<script>window.__ADSGRAM_BLOCK_ID = "__ADSGRAM_BLOCK_ID__";</script>
<style>
  :root {
    --bg: #050010;
    --bg-2: #0a0220;
    --card: rgba(30, 10, 60, 0.55);
    --card-2: rgba(60, 20, 110, 0.6);
    --text: #f1ecff;
    --muted: #a395d6;
    --accent: #b388ff;
    --green: #5eead4;
    --green-2: #14b8a6;
    --gold: #ffc857;
    --line: rgba(180, 140, 255, .12);
  }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  html, body {
    margin: 0; padding: 0;
    background:
      radial-gradient(900px 500px at 80% -10%, #4a1d7a 0%, transparent 55%),
      radial-gradient(700px 500px at 10% 110%, #1a0540 0%, transparent 60%),
      linear-gradient(180deg, #050010 0%, #0a0028 50%, #050010 100%);
    background-attachment: fixed;
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Tahoma, "Cairo", sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
    position: relative;
  }
  /* طبقات النجوم المتحركة */
  .sky { position: fixed; inset: 0; pointer-events: none; overflow: hidden; z-index: 0; }
  .star-layer {
    position: absolute; inset: -50%; width: 200%; height: 200%;
    background-repeat: repeat;
  }
  .star-layer.l1 {
    background-image:
      radial-gradient(1px 1px at 10% 20%, #fff, transparent),
      radial-gradient(1px 1px at 30% 70%, #fff, transparent),
      radial-gradient(1.2px 1.2px at 55% 40%, #fff, transparent),
      radial-gradient(1px 1px at 80% 85%, #fff, transparent),
      radial-gradient(1px 1px at 90% 15%, #fff, transparent),
      radial-gradient(1px 1px at 45% 90%, #fff, transparent);
    background-size: 400px 400px;
    opacity: .85;
    animation: drift1 90s linear infinite, twinkle 3s ease-in-out infinite alternate;
  }
  .star-layer.l2 {
    background-image:
      radial-gradient(1.5px 1.5px at 20% 50%, #d4c1ff, transparent),
      radial-gradient(2px 2px at 65% 25%, #fff, transparent),
      radial-gradient(1.5px 1.5px at 85% 65%, #b388ff, transparent),
      radial-gradient(1px 1px at 15% 80%, #fff, transparent);
    background-size: 600px 600px;
    opacity: .7;
    animation: drift2 140s linear infinite, twinkle 5s ease-in-out infinite alternate;
  }
  .star-layer.l3 {
    background-image:
      radial-gradient(2.5px 2.5px at 40% 30%, #fff, transparent),
      radial-gradient(2px 2px at 75% 75%, #c7a8ff, transparent);
    background-size: 800px 800px;
    opacity: .55;
    animation: drift3 200s linear infinite;
  }
  @keyframes drift1 { from { transform: translate(0,0); } to { transform: translate(-400px,-400px); } }
  @keyframes drift2 { from { transform: translate(0,0); } to { transform: translate(600px,-600px); } }
  @keyframes drift3 { from { transform: translate(0,0); } to { transform: translate(-800px,800px); } }
  @keyframes twinkle { from { opacity: .35; } to { opacity: 1; } }

  /* الشهب المتساقطة */
  .shooting { position: absolute; width: 2px; height: 2px; background: #fff;
    border-radius: 50%; box-shadow: 0 0 8px 2px #fff;
  }
  .shooting::after {
    content:""; position: absolute; top: 50%; right: 0; width: 120px; height: 1px;
    background: linear-gradient(to left, #fff, transparent);
    transform: translateY(-50%);
  }
  .s1 { top: 15%; left: -10%; animation: shoot 7s linear infinite; animation-delay: 1s; }
  .s2 { top: 45%; left: -10%; animation: shoot 11s linear infinite; animation-delay: 4s; }
  .s3 { top: 70%; left: -10%; animation: shoot 9s linear infinite; animation-delay: 7s; }
  @keyframes shoot {
    0% { transform: translate(0,0) rotate(20deg); opacity: 0; }
    10% { opacity: 1; }
    70% { opacity: 1; }
    100% { transform: translate(120vw, 60vh) rotate(20deg); opacity: 0; }
  }

  /* كوكب زحل في الزاوية العلوية */
  .saturn {
    position: fixed; top: 18px; left: 18px;
    width: 110px; height: 110px;
    pointer-events: none; z-index: 1;
    animation: float 8s ease-in-out infinite;
    filter: drop-shadow(0 0 25px rgba(255, 200, 87, 0.35));
  }
  .saturn .ring {
    position: absolute; inset: 0;
    border-radius: 50%;
    transform: rotate(-22deg);
  }
  .saturn .planet {
    position: absolute; top: 22%; left: 22%; width: 56%; height: 56%;
    border-radius: 50%;
    background:
      radial-gradient(circle at 30% 30%, #ffd98a 0%, #f4a52f 35%, #b8651a 70%, #6b3210 100%);
    box-shadow:
      inset -8px -10px 18px rgba(0,0,0,.55),
      inset 4px 5px 10px rgba(255, 235, 180, .35);
  }
  .saturn .planet::before {
    content:""; position: absolute; top: 38%; left: 8%; right: 8%; height: 4px;
    background: rgba(120, 60, 20, .55); border-radius: 50%;
  }
  .saturn .planet::after {
    content:""; position: absolute; top: 58%; left: 12%; right: 16%; height: 3px;
    background: rgba(140, 70, 20, .45); border-radius: 50%;
  }
  .saturn .ring-band {
    position: absolute; top: 50%; left: -8%; right: -8%; height: 14px;
    transform: translateY(-50%);
    border-radius: 50%;
    background: linear-gradient(90deg, transparent 0%, #f0c674 12%, #fff3c4 50%, #f0c674 88%, transparent 100%);
    opacity: .9;
    box-shadow: 0 0 14px rgba(255, 220, 140, .5);
  }
  .saturn .ring-band.inner {
    top: 50%; left: 4%; right: 4%; height: 6px;
    background: linear-gradient(90deg, transparent, #b8821f, transparent);
    opacity: .8;
  }
  @keyframes float {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    50% { transform: translateY(-8px) rotate(2deg); }
  }
  @media (max-width: 380px) {
    .saturn { width: 80px; height: 80px; top: 12px; left: 12px; }
  }
  .container { max-width: 480px; margin: 0 auto; padding: 14px 14px 100px; position: relative; z-index: 2; }
  .topbar { display:flex; align-items:center; justify-content: flex-end; gap:8px; padding: 6px 4px 14px; min-height: 80px; }
  .topbar .logo { font-weight: 800; letter-spacing:.5px; }
  .topbar .logo .bolt { color: var(--gold); margin-inline-start: 4px; }
  .balance-card {
    background: linear-gradient(180deg, rgba(74,29,122,.55), rgba(20,5,50,.75));
    border: 1px solid rgba(180,140,255,.2);
    border-radius: 18px;
    padding: 16px 18px 18px;
    box-shadow: 0 10px 35px rgba(80,30,150,.35), inset 0 1px 0 rgba(255,255,255,.05);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }
  .stat, .tile, .activity, .modal-card { backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); }
  .balance-row { display:flex; justify-content: space-between; align-items: flex-end; }
  .balance-label { color: var(--muted); font-size: 13px; margin-bottom: 4px; }
  .balance-value { display:flex; align-items: baseline; gap: 6px; }
  .balance-value b { font-size: 40px; font-weight: 800; line-height: 1; }
  .balance-value span { color: var(--muted); font-size: 14px; }
  .today { text-align: start; }
  .today b { color: var(--green); font-size: 20px; }
  .today span { color: var(--muted); font-size: 12px; display:block; }
  .dinar { color: var(--muted); font-size: 13px; margin-top: 6px; }
  .progress {
    margin-top: 14px; height: 6px; background: rgba(255,255,255,.06);
    border-radius: 999px; overflow: hidden;
  }
  .progress > div { height: 100%; background: linear-gradient(90deg, #3b82f6, #6ea8ff); border-radius: 999px; transition: width .6s ease; }
  .progress-meta { display:flex; justify-content: space-between; color: var(--muted); font-size: 12px; margin-top: 6px; }
  .stats { display:grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 14px; }
  .stat {
    background: var(--card); border:1px solid var(--line); border-radius: 14px;
    padding: 14px; text-align: center;
  }
  .stat b { font-size: 22px; font-weight: 800; }
  .stat span { display:block; color: var(--muted); font-size: 12px; margin-top: 4px; }
  .grid { display:grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 12px; }
  .tile {
    background: var(--card); border:1px solid var(--line); border-radius: 16px;
    padding: 14px 14px 16px; cursor: pointer; transition: transform .15s, background .15s;
    display:flex; flex-direction: column; align-items: flex-end; gap: 6px;
    text-align: end; min-height: 100px;
  }
  .tile:active { transform: scale(.97); background: var(--card-2); }
  .tile .icon {
    width: 34px; height: 34px; border-radius: 10px;
    background: rgba(110,168,255,.12); color: var(--accent);
    display:grid; place-items:center; font-size: 18px; align-self: flex-end;
  }
  .tile .title { font-weight: 700; font-size: 15px; }
  .tile .sub { color: var(--green); font-size: 12px; }
  .tile.full { grid-column: span 2; flex-direction: row; justify-content: space-between; align-items: center; min-height: 60px; }
  .tile.full .right { text-align: end; }
  .tile.full .icon { background: rgba(251,191,36,.15); color: var(--gold); }
  .activity {
    margin-top: 14px; background: var(--card); border:1px solid var(--line);
    border-radius: 16px; padding: 14px;
  }
  .activity h4 { margin: 0 0 10px; font-size: 14px; color: var(--muted); text-align: end; font-weight: 600; }
  .act-item { display:flex; justify-content: space-between; align-items:center; padding: 8px 0; border-top: 1px solid var(--line); }
  .act-item:first-of-type { border-top: 0; }
  .act-amt { color: var(--green); font-weight: 700; }
  .tabbar {
    position: fixed; bottom: 0; left: 0; right: 0;
    background: rgba(11,16,32,.95); backdrop-filter: blur(10px);
    border-top: 1px solid var(--line); padding: 8px 6px calc(env(safe-area-inset-bottom) + 8px);
    display:grid; grid-template-columns: repeat(6, 1fr); gap: 2px; z-index: 100;
  }
  .tab { display:flex; flex-direction: column; align-items:center; gap:2px; padding: 6px 2px; color: var(--muted); font-size: 10px; cursor: pointer; border-radius: 10px; }
  .tab.active { color: var(--accent); background: rgba(110,168,255,.08); }
  .tab .ti { font-size: 18px; }
  /* Modal */
  .modal-bg { position: fixed; inset: 0; background: rgba(0,0,0,.6); backdrop-filter: blur(4px); display:none; align-items: center; justify-content: center; z-index: 200; padding: 20px; }
  .modal-bg.open { display:flex; }
  .modal {
    background: linear-gradient(180deg, var(--card-2), var(--card));
    border: 1px solid var(--line); border-radius: 18px; padding: 20px;
    width: 100%; max-width: 400px; text-align: center;
    animation: pop .25s ease;
  }
  @keyframes pop { from { transform: scale(.9); opacity: 0 } to { transform: scale(1); opacity: 1 } }
  .modal h3 { margin: 0 0 8px; font-size: 22px; }
  .modal p { color: var(--muted); margin: 6px 0; font-size: 14px; }
  .modal .big { font-size: 36px; font-weight: 800; color: var(--gold); margin: 10px 0; }
  .btn {
    display: inline-block; padding: 12px 22px; border-radius: 12px;
    background: linear-gradient(180deg, var(--green), var(--green-2));
    color: #06281e; font-weight: 700; border: 0; cursor: pointer; font-size: 15px;
    margin-top: 8px; min-width: 140px;
  }
  .btn.alt { background: rgba(255,255,255,.06); color: var(--text); }
  .btn:active { transform: scale(.97); }
  .row { display:flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-top: 10px; }
  /* Wheel */
  .wheel-wrap { position: relative; width: 260px; height: 260px; margin: 10px auto; }
  .wheel { width: 100%; height: 100%; border-radius: 50%; transition: transform 4s cubic-bezier(.17,.67,.21,1); border: 6px solid #3b82f6; box-shadow: 0 0 30px rgba(59,130,246,.4); }
  .pin { position: absolute; top: -10px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 14px solid transparent; border-right: 14px solid transparent; border-top: 22px solid var(--gold); filter: drop-shadow(0 2px 4px rgba(0,0,0,.4)); z-index: 2; }
  .lb-list { text-align: end; max-height: 50vh; overflow-y: auto; padding: 6px 4px; }
  .lb-item { display:flex; justify-content: space-between; padding: 8px 6px; border-bottom: 1px solid var(--line); font-size: 14px; }
  .lb-tabs { display:flex; gap: 6px; margin: 8px 0; justify-content: center; }
  .lb-tab { padding: 6px 14px; border-radius: 999px; background: rgba(255,255,255,.05); color: var(--muted); cursor: pointer; font-size: 13px; }
  .lb-tab.active { background: var(--accent); color: #06122e; font-weight: 700; }
  .invite-link { background: rgba(255,255,255,.05); padding: 10px; border-radius: 10px; word-break: break-all; font-size: 12px; margin: 10px 0; color: var(--accent); border: 1px dashed rgba(110,168,255,.3); }
  .toast { position: fixed; top: 18px; left: 50%; transform: translateX(-50%); background: var(--card-2); border: 1px solid var(--line); padding: 10px 18px; border-radius: 12px; font-size: 14px; z-index: 300; opacity: 0; transition: opacity .25s; pointer-events: none; }
  .toast.show { opacity: 1; }
  .skeleton { background: linear-gradient(90deg, #1a2247 25%, #232c5e 50%, #1a2247 75%); background-size: 200% 100%; animation: shimmer 1.4s infinite; border-radius: 8px; color: transparent; }
  .task-list { display:flex; flex-direction:column; gap:10px; }
  .task-item {
    background: rgba(40,15,80,.55); border:1px solid rgba(180,140,255,.18);
    border-radius: 14px; padding: 12px 14px;
    display:flex; justify-content: space-between; align-items: center; gap: 10px;
  }
  .task-info { text-align: end; flex: 1; }
  .task-title { font-weight: 700; font-size: 14px; margin-bottom: 4px; }
  .task-reward { color: var(--gold); font-size: 12px; font-weight: 600; }
  .task-actions { display:flex; gap:6px; align-items:center; flex-shrink:0; }
  .btn-sub, .btn-verify {
    padding: 8px 14px; border-radius: 10px; font-size: 13px; font-weight: 700;
    border: none; cursor: pointer; text-decoration: none; display:inline-block;
    transition: opacity .15s, transform .1s;
  }
  .btn-sub { background: linear-gradient(135deg, #6d28d9, #b388ff); color:#fff; }
  .btn-verify { background: linear-gradient(135deg, #14b8a6, #5eead4); color:#062c2a; }
  .btn-sub:active, .btn-verify:active { transform: scale(.95); }
  .btn-verify:disabled { opacity:.5; cursor:not-allowed; }
  .badge.done { background: rgba(94,234,212,.15); color: var(--green); padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 700; }
  @keyframes shimmer { 0% { background-position: 200% 0 } 100% { background-position: -200% 0 } }
</style>
</head>
<body>
  <div class="sky" aria-hidden="true">
    <div class="star-layer l1"></div>
    <div class="star-layer l2"></div>
    <div class="star-layer l3"></div>
    <div class="shooting s1"></div>
    <div class="shooting s2"></div>
    <div class="shooting s3"></div>
  </div>
  <div class="saturn" aria-hidden="true">
    <div class="ring">
      <div class="ring-band"></div>
      <div class="planet"></div>
      <div class="ring-band inner"></div>
    </div>
  </div>
  <div class="container">
    <div class="topbar">
      <div class="logo">⚡ <span>شبكتي</span></div>
    </div>

    <div class="balance-card">
      <div class="balance-row">
        <div class="today">
          <span class="balance-label">اليوم</span>
          <b id="today">+0</b>
          <span>النقاط المكتسبة</span>
        </div>
        <div style="text-align:end">
          <div class="balance-label">رصيدك</div>
          <div class="balance-value">
            <b id="points" class="skeleton">000</b>
            <span>نقطة</span>
          </div>
          <div class="dinar">= <span id="dinar">0.00</span> دينار جزائري</div>
        </div>
      </div>
      <div class="progress"><div id="bar" style="width:0%"></div></div>
      <div class="progress-meta">
        <span id="goal">5,000 نقطة للسحب</span>
        <span><span id="cur">0</span> / <span id="min">5000</span></span>
      </div>
    </div>

    <div class="stats">
      <div class="stat"><b id="s-refs">0</b><span>الإحالات</span></div>
      <div class="stat"><b id="s-ads">0</b><span>إعلانات</span></div>
      <div class="stat"><b id="s-tasks">0</b><span>المهام</span></div>
    </div>

    <div class="grid">
      <div class="tile" data-action="ad">
        <div class="icon">🎬</div>
        <div class="title">شاهد الإعلانات</div>
        <div class="sub">+20 نقطة لكل منها</div>
      </div>
      <div class="tile" data-action="task">
        <div class="icon">📋</div>
        <div class="title">إنجاز المهام</div>
        <div class="sub">+50 نقطة لكل منها</div>
      </div>
      <div class="tile" data-action="invite">
        <div class="icon">👥</div>
        <div class="title">ادعُ الأصدقاء</div>
        <div class="sub">+100 نقطة لكل منها</div>
      </div>
      <div class="tile" data-action="withdraw">
        <div class="icon">💰</div>
        <div class="title">يسحب</div>
        <div class="sub">الحد الأدنى 5,000 نقطة</div>
      </div>
      <div class="tile" data-action="spin">
        <div class="icon">🎡</div>
        <div class="title">عجلة الحظ</div>
        <div class="sub">مرة كل ساعة</div>
      </div>
      <div class="tile" data-action="mystery">
        <div class="icon">🎁</div>
        <div class="title">صندوق غامض</div>
        <div class="sub">ربح أو خسارة</div>
      </div>
      <div class="tile full" data-action="daily">
        <div style="display:flex; align-items:center; gap: 12px;">
          <div class="icon">🎁</div>
          <div class="right">
            <div class="title">المكافأة اليومية</div>
            <div class="sub">+75 نقطة كل 24 ساعة</div>
          </div>
        </div>
        <div style="color:var(--muted); font-size:12px" id="daily-status">متاحة</div>
      </div>
    </div>

    <div class="activity">
      <h4>النشاط الأخير</h4>
      <div id="activity-list">
        <div class="act-item"><div>مرحباً بك في شبكتي 👋</div><div class="act-amt">+0</div></div>
      </div>
    </div>
  </div>

  <div class="tabbar">
    <div class="tab active" data-tab="home"><div class="ti">⚡</div><div>بيت</div></div>
    <div class="tab" data-tab="tasks"><div class="ti">📋</div><div>المهام</div></div>
    <div class="tab" data-tab="ads"><div class="ti">🎬</div><div>إعلانات</div></div>
    <div class="tab" data-tab="invite"><div class="ti">👥</div><div>يدعو</div></div>
    <div class="tab" data-tab="withdraw"><div class="ti">💵</div><div>يسحب</div></div>
    <div class="tab" data-tab="leaderboard"><div class="ti">🏆</div><div>الترتيب</div></div>
  </div>

  <div class="modal-bg" id="modal">
    <div class="modal" id="modal-body"></div>
  </div>

  <div class="toast" id="toast"></div>

<script>
  const tg = window.Telegram?.WebApp;
  if (tg) { tg.ready(); tg.expand(); try { tg.setHeaderColor('#0b1020'); tg.setBackgroundColor('#0b1020'); } catch(e){} }

  const initData = tg?.initData || '';
  const API = (path) => '/api/miniapp' + path;
  const ACTIVITY = [];

  async function api(path, body = {}) {
    const r = await fetch(API(path), {
      method: 'POST',
      headers: { 'Content-Type':'application/json', 'X-Telegram-Init-Data': initData },
      body: JSON.stringify(body),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw Object.assign(new Error(data.error || 'error'), { status: r.status, data });
    return data;
  }

  function fmt(n) { return new Intl.NumberFormat('ar-EG').format(n); }
  function fmtTime(s) {
    s = Math.max(0, Math.floor(s));
    const h = Math.floor(s/3600), m = Math.floor((s%3600)/60), sec = s%60;
    if (h) return h+'س '+m+'د';
    if (m) return m+'د '+sec+'ث';
    return sec+'ث';
  }
  function toast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg; t.classList.add('show');
    clearTimeout(window._tt); window._tt = setTimeout(() => t.classList.remove('show'), 2200);
  }
  function escHtml(s) { return String(s||'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

  async function openTasksModal() {
    openModal('<h3>📋 المهام</h3><p style="color:var(--muted)">جارٍ التحميل...</p>');
    let data;
    try { data = await api('/tasks/list'); }
    catch (e) { closeModal(); return toast('تعذر تحميل المهام'); }
    const items = (data.tasks || []).map(function(t) {
      var done = t.completed;
      var reward = '+' + t.reward + ' نقطة';
      var actions = done
        ? '<span class="badge done">✅ مكتملة</span>'
        : '<a class="btn-sub" href="' + escHtml(t.link) + '" target="_blank" rel="noopener">اشترك</a>'
          + '<button class="btn-verify" data-task="' + escHtml(t.id) + '">تحقّق</button>';
      return '<div class="task-item">'
        + '<div class="task-info">'
        +   '<div class="task-title">' + escHtml(t.title) + '</div>'
        +   '<div class="task-reward">' + reward + '</div>'
        + '</div>'
        + '<div class="task-actions">' + actions + '</div>'
        + '</div>';
    }).join('') || '<p style="color:var(--muted)">لا توجد مهام حالياً</p>';
    openModal(
      '<h3 style="margin-bottom:8px">📋 المهام المتاحة</h3>' +
      '<p style="color:var(--muted);font-size:13px;margin:0 0 14px">اشترك في القنوات ثم اضغط «تحقّق» لاستلام النقاط</p>' +
      '<div class="task-list">' + items + '</div>' +
      '<button class="btn" style="margin-top:14px" onclick="closeModal()">إغلاق</button>'
    );
    document.querySelectorAll('.btn-verify').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.task;
        btn.disabled = true; btn.textContent = '...';
        haptic('light');
        try {
          const r = await api('/tasks/claim', { taskId: id });
          notify('success'); render(r); pushActivity('📋 ' + (r.taskId || 'مهمة'), r.reward);
          openModal('<h3>✅ تم!</h3><div class="big">+'+r.reward+'</div><p>نقطة أُضيفت لرصيدك</p><button class="btn" onclick="openTasksModal()">العودة للمهام</button>');
        } catch (e) {
          notify('warning');
          const msg = (e.data && e.data.message) || 'تعذر التحقق';
          btn.disabled = false; btn.textContent = 'تحقّق';
          toast(msg);
        }
      });
    });
  }

  function render(s) {
    document.getElementById('points').textContent = fmt(s.points);
    document.getElementById('points').classList.remove('skeleton');
    document.getElementById('dinar').textContent = (s.points / s.pointsPerDinar).toFixed(2);
    document.getElementById('cur').textContent = fmt(s.points);
    document.getElementById('min').textContent = fmt(s.withdrawMin);
    document.getElementById('goal').textContent = fmt(s.withdrawMin) + ' نقطة للسحب';
    const pct = Math.min(100, (s.points / s.withdrawMin) * 100);
    document.getElementById('bar').style.width = pct + '%';
    document.getElementById('s-refs').textContent = fmt(s.referrals);
    document.getElementById('s-ads').textContent = fmt(s.adsWatched);
    document.getElementById('s-tasks').textContent = fmt(s.tasksDone);
    document.getElementById('daily-status').textContent =
      s.cooldowns.daily > 0 ? 'بعد ' + fmtTime(s.cooldowns.daily) : 'متاحة الآن';
  }

  function pushActivity(label, amt) {
    ACTIVITY.unshift({ label, amt });
    if (ACTIVITY.length > 6) ACTIVITY.pop();
    document.getElementById('activity-list').innerHTML = ACTIVITY.map(a =>
      '<div class="act-item"><div>'+a.label+'</div><div class="act-amt">'+(a.amt>=0?'+':'')+a.amt+'</div></div>'
    ).join('');
  }

  function openModal(html) {
    document.getElementById('modal-body').innerHTML = html;
    document.getElementById('modal').classList.add('open');
  }
  function closeModal() { document.getElementById('modal').classList.remove('open'); }
  document.getElementById('modal').addEventListener('click', (e) => {
    if (e.target.id === 'modal') closeModal();
  });

  async function load() {
    try {
      const s = await api('/me');
      render(s);
    } catch (e) {
      document.getElementById('points').textContent = '—';
      document.getElementById('points').classList.remove('skeleton');
      openModal('<h3>⚠️ تعذر التحقق</h3><p>افتح هذا التطبيق من داخل بوت تيليجرام.</p><button class="btn" onclick="closeModal()">حسناً</button>');
    }
  }

  function haptic(type='light') { try { tg?.HapticFeedback?.impactOccurred(type); } catch(e){} }
  function notify(type='success') { try { tg?.HapticFeedback?.notificationOccurred(type); } catch(e){} }

  async function doAction(action) {
    haptic('light');
    if (action === 'ad') {
      try {
        const blockId = window.__ADSGRAM_BLOCK_ID;
        if (blockId && window.Adsgram) {
          if (!window.__adsgramCtl) {
            window.__adsgramCtl = window.Adsgram.init({ blockId });
          }
          openModal('<h3>🎬 جارٍ تحميل الإعلان...</h3><p>سيتم فتح الإعلان بعد لحظات</p>');
          try {
            await window.__adsgramCtl.show();
          } catch (adErr) {
            closeModal();
            notify('warning');
            const code = adErr && (adErr.error || adErr.code || adErr.description);
            if (code === 'NoAd' || code === 'no-ad' || (typeof code === 'string' && code.toLowerCase().includes('no'))) {
              toast('لا توجد إعلانات متاحة الآن، حاول لاحقاً');
            } else {
              toast('تم إلغاء الإعلان');
            }
            return;
          }
        } else {
          openModal('<h3>🎬 يتم تشغيل الإعلان...</h3><p>انتظر 5 ثواني للحصول على المكافأة</p><div class="big" id="ad-cd">5</div>');
          let n = 5;
          await new Promise(res => {
            const it = setInterval(() => {
              n--; const el = document.getElementById('ad-cd'); if (el) el.textContent = n;
              if (n <= 0) { clearInterval(it); res(); }
            }, 1000);
          });
        }
        const r = await api('/ad');
        notify('success');
        render(r); pushActivity('🎬 مشاهدة إعلان', r.reward);
        openModal('<h3>✅ تم!</h3><div class="big">+'+r.reward+'</div><p>نقطة أُضيفت لرصيدك</p><button class="btn" onclick="closeModal()">رائع</button>');
      } catch (e) {
        notify('warning');
        if (e.status === 429) toast('⏳ انتظر '+fmtTime(e.data.wait));
        else toast('حدث خطأ');
        closeModal();
      }
    } else if (action === 'task') {
      await openTasksModal();
    } else if (action === 'daily') {
      try {
        const r = await api('/daily');
        notify('success'); render(r); pushActivity('🎁 مكافأة يومية', r.reward);
        openModal('<h3>🎁 المكافأة اليومية</h3><div class="big">+'+r.reward+'</div><p>عُد غداً للمزيد</p><button class="btn" onclick="closeModal()">شكراً</button>');
      } catch (e) { notify('warning'); if (e.status === 429) toast('⏳ متاحة بعد '+fmtTime(e.data.wait)); }
    } else if (action === 'mystery') {
      try {
        const r = await api('/mystery');
        notify(r.result.delta >= 0 ? 'success' : 'warning'); render(r);
        pushActivity('🎁 صندوق غامض', r.result.delta);
        openModal('<h3>'+r.result.label+'</h3><div class="big">'+(r.result.delta>=0?'+':'')+r.result.delta+'</div><p>نقطة</p><button class="btn" onclick="closeModal()">حسناً</button>');
      } catch (e) { toast('حدث خطأ'); }
    } else if (action === 'spin') openSpin();
    else if (action === 'invite') openInvite();
    else if (action === 'withdraw') openWithdraw();
    else if (action === 'leaderboard') openLeaderboard();
  }

  async function openSpin() {
    try {
      openModal('<h3>🎡 عجلة الحظ</h3><div class="wheel-wrap"><div class="pin"></div><div class="wheel" id="wheel"></div></div><p id="spin-msg">اضغط للف</p><button class="btn" id="spin-btn">🎲 لف العجلة</button>');
      const wheel = document.getElementById('wheel');
      const prizes = [10, 20, 50, 100, 10, 20, 0, 50];
      const slice = 360 / prizes.length;
      const colors = ['#3b82f6','#6ea8ff','#34d399','#fbbf24','#3b82f6','#6ea8ff','#64748b','#34d399'];
      let grad = 'conic-gradient(';
      prizes.forEach((p, i) => {
        grad += colors[i]+' '+(i*slice)+'deg '+((i+1)*slice)+'deg'+(i<prizes.length-1?',':'');
      });
      grad += ')';
      wheel.style.background = grad;
      wheel.innerHTML = prizes.map((p, i) => {
        const ang = i*slice + slice/2;
        return '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate('+ang+'deg) translateY(-90px); color:#fff; font-weight:800; font-size:14px">'+p+'</div>';
      }).join('');
      wheel.style.position = 'relative';
      document.getElementById('spin-btn').onclick = async () => {
        document.getElementById('spin-btn').disabled = true;
        try {
          const r = await api('/spin');
          const idx = prizes.indexOf(r.prize);
          const target = 360 * 6 + (360 - (idx * slice + slice/2));
          wheel.style.transform = 'rotate('+target+'deg)';
          setTimeout(() => {
            notify(r.prize > 0 ? 'success' : 'warning');
            render(r);
            pushActivity('🎡 عجلة الحظ', r.prize);
            openModal('<h3>'+(r.prize>0?'🎉 مبروك!':'😅 حظ أوفر')+'</h3><div class="big">+'+r.prize+'</div><p>نقطة</p><button class="btn" onclick="closeModal()">رائع</button>');
          }, 4200);
        } catch (e) {
          if (e.status === 429) {
            document.getElementById('spin-msg').innerHTML = '⏳ متاحة بعد <b>'+fmtTime(e.data.wait)+'</b>';
            document.getElementById('spin-btn').textContent = 'حسناً';
            document.getElementById('spin-btn').disabled = false;
            document.getElementById('spin-btn').onclick = closeModal;
          }
        }
      };
    } catch (e) { toast('حدث خطأ'); }
  }

  async function openInvite() {
    try {
      const r = await api('/invite');
      const link = r.link || '—';
      openModal(
        '<h3>👥 ادعُ أصدقاءك</h3>'+
        '<p>اربح <b>+'+r.reward+'</b> نقطة لكل صديق ينضم</p>'+
        '<div class="invite-link">'+link+'</div>'+
        '<div class="row">'+
          '<button class="btn" id="copy-btn">📋 نسخ الرابط</button>'+
          '<button class="btn alt" onclick="closeModal()">إغلاق</button>'+
        '</div>'+
        '<p style="margin-top:10px">إحالاتك: <b>'+r.referrals+'</b></p>'
      );
      document.getElementById('copy-btn').onclick = () => {
        try { tg?.openTelegramLink && tg.openTelegramLink('https://t.me/share/url?url='+encodeURIComponent(link)+'&text='+encodeURIComponent('انضم واربح نقاط مجانية!')); }
        catch(e){}
        navigator.clipboard?.writeText(link).then(() => toast('✅ تم النسخ'));
      };
    } catch (e) { toast('حدث خطأ'); }
  }

  async function openWithdraw() {
    try {
      const s = await api('/me');
      if (s.points < s.withdrawMin) {
        const need = s.withdrawMin - s.points;
        openModal('<h3>💰 طلب سحب</h3><p>رصيدك غير كافٍ</p><p>رصيدك: <b>'+fmt(s.points)+'</b></p><p>الحد الأدنى: <b>'+fmt(s.withdrawMin)+'</b></p><p>ينقصك: <b style="color:var(--gold)">'+fmt(need)+'</b> نقطة</p><button class="btn alt" onclick="closeModal()">حسناً</button>');
        return;
      }
      openModal('<h3>💰 تأكيد السحب</h3><p>سيتم خصم <b>'+fmt(s.withdrawMin)+'</b> نقطة</p><p style="color:var(--gold)">= '+(s.withdrawMin/s.pointsPerDinar).toFixed(2)+' دينار</p><div class="row"><button class="btn" id="conf">✅ تأكيد</button><button class="btn alt" onclick="closeModal()">إلغاء</button></div>');
      document.getElementById('conf').onclick = async () => {
        try {
          const r = await api('/withdraw');
          notify('success'); render(r); pushActivity('💰 طلب سحب', -r.amount);
          openModal('<h3>✅ تم تسجيل طلب السحب!</h3><div class="big">'+(r.amount/r.pointsPerDinar).toFixed(2)+'</div><p>دينار جزائري</p><p>سيُراجع طلبك خلال 24-48 ساعة.</p><button class="btn" onclick="closeModal()">رائع</button>');
        } catch (e) { toast('حدث خطأ في السحب'); }
      };
    } catch (e) { toast('حدث خطأ'); }
  }

  async function openLeaderboard() {
    try {
      const r = await api('/leaderboard');
      const medals = ['🥇','🥈','🥉','🔹','🔹','🔹','🔹','🔹','🔹','🔹'];
      const renderTab = (rows, suffix) => rows.length
        ? rows.map((u, i) => '<div class="lb-item"><div>'+medals[i]+' '+(u.full_name || u.username || ('User'+u.user_id))+'</div><div><b>'+fmt(u.val)+'</b> '+suffix+'</div></div>').join('')
        : '<p style="color:var(--muted)">لا يوجد بعد</p>';
      const pHtml = renderTab(r.byPoints, 'نقطة');
      const refHtml = renderTab(r.byReferrals, 'إحالة');
      openModal(
        '<h3>🏆 الترتيب</h3>'+
        '<div class="lb-tabs"><div class="lb-tab active" id="lb-p">💎 النقاط</div><div class="lb-tab" id="lb-r">👥 الإحالات</div></div>'+
        '<div class="lb-list" id="lb-list">'+pHtml+'</div>'+
        '<button class="btn alt" onclick="closeModal()" style="margin-top:10px">إغلاق</button>'
      );
      document.getElementById('lb-p').onclick = () => {
        document.getElementById('lb-p').classList.add('active');
        document.getElementById('lb-r').classList.remove('active');
        document.getElementById('lb-list').innerHTML = pHtml;
      };
      document.getElementById('lb-r').onclick = () => {
        document.getElementById('lb-r').classList.add('active');
        document.getElementById('lb-p').classList.remove('active');
        document.getElementById('lb-list').innerHTML = refHtml;
      };
    } catch (e) { toast('حدث خطأ'); }
  }

  document.querySelectorAll('.tile').forEach(t => {
    t.addEventListener('click', () => doAction(t.dataset.action));
  });
  document.querySelectorAll('.tab').forEach(t => {
    t.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
      t.classList.add('active');
      const tab = t.dataset.tab;
      if (tab === 'home') return;
      doAction(tab);
    });
  });

  load();
</script>
</body>
</html>`;
