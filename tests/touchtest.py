# 터치 영역 점검: 터치 기기에서 화면마다 누를 수 있는 요소의 "실제로 눌리는 범위"를 잰다.
# 눈에 보이는 버튼 크기가 아니라, 손가락이 닿는 점에서 브라우저가 그 버튼을 고르는 범위(elementFromPoint)를 잰다.
#  - 실제 터치 영역은 가로·세로 44 CSS px 이상 (휴대폰 가로 화면 포함)
#  - 버튼이 보이는 자기 영역은 다른 요소에 빼앗기지 않는다 (터치 영역 겹침 검사)
#  - 휴대폰 가로 화면에서 훈련 틀이 100px 이상 보인다
# 마우스 기기(MacBook)는 기존 디자인 유지를 위해 크기 기준을 적용하지 않고, 빠르기 −/+ 36px 그대로인지만 본다.
import os, json
from playwright.sync_api import sync_playwright
URL = 'file://' + __import__('pathlib').Path(__file__).resolve().parent.parent.joinpath('index.html').as_posix()
ENGINE = os.environ.get('BROWSER', 'chromium')
MIN = 44
PROFILES = [  # 이름, 너비, 높이, 터치
    ('phone-320', 320, 640, True), ('phone', 390, 844, True), ('phone-land', 844, 390, True), ('android-land', 740, 360, True),
    ('ipad', 820, 1180, True), ('ipad-land', 1180, 820, True), ('ipad-split', 590, 820, True), ('ipad-slideover', 320, 980, True),
    ('macbook', 1440, 900, False),
]
COMBOS = [('ko-KR', 'light'), ('en-US', 'dark')]
NAV = "l => [...document.querySelectorAll('#tabbar button, .nav button')].find(b => b.offsetParent && b.textContent == l).click()"
AUDIT = r"""() => {
  const scr = document.querySelector('.screen.on');
  const roots = [scr, ...document.querySelectorAll('.top, #tabbar, .nav')].filter(Boolean);
  const seen = new Set(), list = [];
  for (const root of roots) for (const el of root.querySelectorAll('button, a[href], input[type=range], label')) {
    if (seen.has(el)) continue; seen.add(el);
    if (el.tagName === 'LABEL' && !el.querySelector('input[type=checkbox], input[type=radio]')) continue;
    if (el.disabled || !el.offsetParent) continue;
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || cs.pointerEvents === 'none') continue;
    const ov = el.closest('.ovl'); if (ov && !ov.classList.contains('on')) continue;
    const r = el.getBoundingClientRect(); if (r.width < 1 || r.height < 1) continue;
    list.push(el);
  }
  const owns = (el, x, y) => {
    if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) return true;   // 화면 가장자리 너머는 손가락이 가장자리에 닿는다
    const t = document.elementFromPoint(x, y); return !!t && (t === el || el.contains(t));
  };
  const out = [];
  for (const el of list) {
    el.scrollIntoView({ block: 'center', inline: 'nearest' });
    const r = el.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    const name = (el.id ? '#' + el.id : el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/)[0] : ''))
               + ' "' + (el.textContent || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 14) + '"';
    if (!owns(el, cx, cy)) { out.push({ name, covered: true }); continue; }
    const reach = (dx, dy) => { let n = 0; while (n < 60 && owns(el, cx + dx * (n + 1), cy + dy * (n + 1))) n++; return n; };
    const w = reach(-1, 0) + reach(1, 0) + 1, h = reach(0, -1) + reach(0, 1) + 1;
    // 보이는 자기 영역(가장자리 2px 안쪽)이 다른 요소에 빼앗기지 않는지
    let stolen = null;
    // 둥근 버튼은 모서리 바깥이 원래 버튼이 아니므로, 둥근 끝 안쪽의 가로·세로 중심선 위 점만 본다
    const cap = Math.min(r.width, r.height) / 2;
    for (const [x, y] of [[cx, cy], [r.left + cap, cy], [r.right - cap, cy], [cx, r.top + 2], [cx, r.bottom - 2]]) {
      if (!owns(el, x, y)) { const t = document.elementFromPoint(x, y); stolen = t ? (t.id || t.className || t.tagName) : null; }
    }
    out.push({ name, vis: [Math.round(r.width), Math.round(r.height)], hit: [Math.min(w, 121), Math.min(h, 121)], stolen });
  }
  window.scrollTo(0, 0);
  return out;
}"""
errs, report = [], {}
def check(c, m):
    if not c: errs.append(m)
with sync_playwright() as p:
    b = getattr(p, ENGINE).launch()
    for name, w, h, touch in PROFILES:
      for loc, theme in COMBOS:
        ctx = b.new_context(viewport={'width': w, 'height': h}, locale=loc, has_touch=touch, is_mobile=touch and ENGINE != 'firefox',
                            color_scheme=theme, device_scale_factor=1)
        pg = ctx.new_page(); pe = []; pg.on('pageerror', lambda e: pe.append(str(e)))
        pg.clock.install(); pg.goto(URL); pg.wait_for_timeout(200)
        shots = {}
        def audit(label):
            shots[label] = pg.evaluate(AUDIT)
        audit('dash')
        for lab, sid in [('Training', 'train'), ('Test', 'test'), ('Progress', 'prog'), ('Curriculum', 'curr'), ('Dashboard', 'dash')]:
            pg.evaluate(NAV, lab); pg.wait_for_timeout(80)
            if sid != 'dash': audit(sid)
        pg.click('#todayRows li:nth-child(1) button'); pg.wait_for_timeout(150)
        if pg.evaluate("document.querySelector('#calib').classList.contains('on')"):
            audit('calib'); pg.click('#calibSave'); pg.wait_for_timeout(150)
        audit('brief')
        pg.click('#segTime button:nth-child(2)'); pg.click('#briefGo'); pg.clock.run_for(3500); pg.wait_for_timeout(100)
        audit('player')
        st = pg.evaluate("Math.round(document.querySelector('#stage').getBoundingClientRect().height)")
        if w > h and h <= 500: check(st >= 100, f'{name} {loc} stage too small {st}')
        pg.click('#pauseBtn'); pg.wait_for_timeout(100); audit('pause'); pg.click('#resumeBtn'); pg.wait_for_timeout(100)
        pg.clock.run_for(16000); pg.clock.run_for(6000); pg.clock.run_for(31000); pg.wait_for_timeout(150)
        if pg.evaluate("document.querySelector('#check').classList.contains('on')"):
            audit('check'); pg.click('#toResult'); pg.wait_for_timeout(100); audit('result')
        # 독서활동 R.M.
        pg.goto(URL); pg.wait_for_timeout(150); pg.evaluate(NAV, 'Training'); pg.wait_for_timeout(80)
        rm = pg.query_selector("#trList button:has-text('R.M')")
        if rm:
            rm.click(); pg.wait_for_timeout(150)
            if pg.evaluate("document.querySelector('#calib').classList.contains('on')"): pg.click('#calibSave'); pg.wait_for_timeout(150)
            pg.click('#segTime button:nth-child(1)'); pg.click('#briefGo'); pg.clock.run_for(3500); pg.wait_for_timeout(100)
            if pg.evaluate("document.querySelector('#rm').classList.contains('on')"): audit('rm')
            else: check(False, f'{name} {loc} R.M. screen not opened')
        else: check(False, f'{name} {loc} R.M. row not found')
        # 1분 측정
        pg.goto(URL); pg.wait_for_timeout(150); pg.evaluate(NAV, 'Test'); pg.wait_for_timeout(80)
        pg.click('#teList li:nth-child(1) button'); pg.wait_for_timeout(150)
        if pg.evaluate("document.querySelector('#brief').classList.contains('on')"): pg.click('#briefGo'); pg.wait_for_timeout(150)
        pg.clock.run_for(4000); pg.wait_for_timeout(100)
        if pg.evaluate("document.querySelector('#mread').classList.contains('on')"):
            audit('mread')   # 문제 화면(mquiz)의 보기·척도 버튼은 높이 46~52px로 CSS에서 확인 (이 테스트에서는 들어가지 않음)
        else: check(False, f'{name} {loc} 1-minute reading screen not opened')
        bad = []
        for scr, items in shots.items():
            for it in items:
                if it.get('covered'): bad.append((scr, it['name'], 'covered')); continue
                if it['stolen']: bad.append((scr, it['name'], 'overlap', it['stolen']))
                if touch and (it['hit'][0] < MIN or it['hit'][1] < MIN): bad.append((scr, it['name'], 'hit', it['hit'], 'vis', it['vis']))
        if not touch:
            pace = [it for it in shots.get('player', []) if '#pace' in it['name']]
            check(pace and all(it['vis'] == [36, 36] for it in pace), f'{name} desktop pace buttons changed {pace}')
        report[f'{name} {loc} {theme}'] = {s: [(it['name'], it.get('vis'), it.get('hit')) for it in v] for s, v in shots.items()}
        print(ENGINE, name, loc, theme, 'screens', len(shots), 'OK' if not bad and not pe else ('BAD', bad, pe))
        if bad or pe: errs.append((name, loc, theme, bad, pe))
        ctx.close()
    b.close()
if os.environ.get('TOUCH_REPORT'): open(os.environ['TOUCH_REPORT'], 'w').write(json.dumps(report, ensure_ascii=False, indent=1))
print('ERR', errs)
