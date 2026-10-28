# 반응 점검 화면 선택 버튼: 선택 전후 구분과 WCAG 대비(글자 4.5:1, 테두리·상태 3:1)를 라이트/다크·ko/en·휴대폰/데스크톱에서 자동 검사
from playwright.sync_api import sync_playwright
URL='file://' + __import__('pathlib').Path(__file__).resolve().parent.parent.joinpath('index.html').as_posix()
JS = """() => {
  const rgb = s => s.match(/[\\d.]+/g).slice(0,3).map(Number);
  const lum = c => { const v = c.map(x => { x /= 255; return x <= 0.03928 ? x/12.92 : Math.pow((x+0.055)/1.055, 2.4); }); return 0.2126*v[0]+0.7152*v[1]+0.0722*v[2]; };
  const cr = (a, b) => { const x = lum(rgb(a)), y = lum(rgb(b)); return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05); };
  const page = getComputedStyle(document.body).backgroundColor;
  const out = [];
  for (const sel of ['#segBlink button', '#segBlinkFirst button', '#chips button']){
    const bs = [...document.querySelectorAll(sel)];
    const on = bs.find(b => b.getAttribute('aria-pressed') === 'true'), off = bs.find(b => b.getAttribute('aria-pressed') !== 'true');
    const a = getComputedStyle(on), b = getComputedStyle(off);
    out.push({ sel,
      onText: cr(a.color, a.backgroundColor), offText: cr(b.color, b.backgroundColor),
      onVsPage: cr(a.backgroundColor, page), offBorder: Math.min(cr(b.borderTopColor, page), cr(b.borderTopColor, b.backgroundColor)),
      onVsOff: cr(a.backgroundColor, b.backgroundColor),
      check: getComputedStyle(on, '::before').content, offCheck: getComputedStyle(off, '::before').content });
  }
  const t = document.querySelector('#segTime button[aria-pressed="true"]');
  return { out, timeSel: t ? getComputedStyle(t).backgroundColor : null, ink: getComputedStyle(document.documentElement).getPropertyValue('--ink').trim() };
}"""
errs = []
with sync_playwright() as p:
    b = getattr(p, __import__("os").environ.get("BROWSER", "chromium")).launch()
    for scheme in ['light', 'dark']:
      for loc, vp, mob in [('ko-KR', (360, 740), True), ('en-US', (1366, 900), False), ('en-US', (390, 844), True), ('ko-KR', (1366, 900), False)]:
        pg = b.new_page(viewport={'width': vp[0], 'height': vp[1]}, locale=loc, color_scheme=scheme, is_mobile=mob, has_touch=mob)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.clock.install(); pg.goto(URL); pg.wait_for_timeout(200)
        pg.click('#todayRows li:nth-child(1) button'); pg.wait_for_timeout(100)
        if pg.evaluate("document.querySelector('#calib').classList.contains('on')"): pg.click('#calibSave'); pg.wait_for_timeout(150)
        pg.click('#segTime button:nth-child(2)')
        brief_sel = pg.evaluate("getComputedStyle(document.querySelector('#segTime button[aria-pressed=\"true\"]')).backgroundColor")
        pg.click('#briefGo'); pg.clock.run_for(3500); pg.clock.run_for(16000); pg.clock.run_for(6000); pg.clock.run_for(31000); pg.wait_for_timeout(150)
        pg.click('#segBlink button:nth-child(3)'); pg.click('#segBlinkFirst button:nth-child(2)'); pg.click('#chips button:nth-child(1)')
        r = pg.evaluate(JS)
        for o in r['out']:
            bad = [k for k, lim in [('onText', 4.5), ('offText', 4.5), ('onVsPage', 3), ('offBorder', 3), ('onVsOff', 3)] if o[k] < lim]
            if '2713' not in o['check'].encode('unicode_escape').decode() and o['check'] != '"✓"': bad.append('no check mark')
            if o['offCheck'] not in ('none', 'normal'): bad.append('check on unselected')
            if bad: errs.append(f"{scheme} {loc} {vp} {o['sel']} {bad} {o}")
        # 다른 화면(훈련 전 안내)의 선택 버튼은 기존 스타일(ink 바탕) 그대로
        ink = pg.evaluate("getComputedStyle(document.body).color")
        if brief_sel != ink: errs.append(f'brief seg changed {brief_sel} vs {ink}')
        # 선택 해제·전환 동작 그대로
        pg.click('#chips button:nth-child(1)')
        if pg.evaluate("document.querySelector('#chips button:nth-child(1)').getAttribute('aria-pressed')") != 'false': errs.append('chip toggle off failed')
        sx = {k: round(v, 2) for k, v in r['out'][2].items() if isinstance(v, float)}
        print(scheme, loc, vp, 'chips', sx)
        pg.close()
print('ERR', errs)
