# 기기 크기별 호환성 훑기: 주요 화면의 가로 넘침, 훈련 화면이 창 안에 들어오는지, 스크립트 오류
# BROWSER=chromium(기본) 또는 webkit. webkit은 Safari와 같은 엔진 계열이지만 실제 Safari와 똑같지는 않다.
import os
from playwright.sync_api import sync_playwright
URL = 'file://' + __import__('pathlib').Path(__file__).resolve().parent.parent.joinpath('index.html').as_posix()
ENGINE = os.environ.get('BROWSER', 'chromium')
PROFILES = [  # 이름, 너비, 높이, 터치 기기, 배율
    ('android-phone', 360, 740, True, 3), ('android-phone-land', 740, 360, True, 3),
    ('ipad-portrait', 820, 1180, True, 2), ('ipad-land', 1180, 820, True, 2),
    ('ipad-slideover', 320, 980, True, 2), ('ipad-split-half', 590, 820, True, 2),
    ('macbook', 1440, 900, False, 2), ('macbook-small', 1280, 720, False, 2),
]
NAV = "l => [...document.querySelectorAll('#tabbar button, .nav button')].find(b => b.offsetParent && b.textContent == l).click()"
over = "(() => document.documentElement.scrollWidth - innerWidth)()"
errs = []
with sync_playwright() as p:
    b = getattr(p, ENGINE).launch()
    for name, w, h, touch, dpr in PROFILES:
      for loc in ['ko-KR', 'en-US']:
        ctx = b.new_context(viewport={'width': w, 'height': h}, locale=loc, has_touch=touch, device_scale_factor=dpr,
                            is_mobile=touch and ENGINE != 'firefox')
        pg = ctx.new_page(); pe = []; pg.on('pageerror', lambda e: pe.append(str(e)))
        pg.clock.install(); pg.goto(URL); pg.wait_for_timeout(200)
        bad = []
        for lab in ['Progress', 'Curriculum', 'Dashboard']:
            pg.evaluate(NAV, lab); pg.wait_for_timeout(80)
            o = pg.evaluate(over)
            if o > 1: bad.append((lab, o))
        pg.click('#todayRows li:nth-child(1) button'); pg.wait_for_timeout(150)
        if pg.evaluate("document.querySelector('#calib').classList.contains('on')"):
            o = pg.evaluate(over)
            if o > 1: bad.append(('calib', o))
            pg.click('#calibSave'); pg.wait_for_timeout(150)
        o = pg.evaluate(over)
        if o > 1: bad.append(('brief', o))
        pg.click('#segTime button:nth-child(2)'); pg.click('#briefGo'); pg.clock.run_for(3500); pg.wait_for_timeout(100)
        # 훈련 화면: 원 배치(svg)가 창 안에 다 보여야 한다
        r = pg.evaluate("(() => { const s = document.querySelector('#stage').getBoundingClientRect(); return [Math.round(s.left), Math.round(s.right), Math.round(s.bottom), innerWidth, innerHeight]; })()")
        if r[0] < -1 or r[1] > r[3] + 1: bad.append(('player-x', r))
        if r[2] > r[4] + 1: bad.append(('player-below-fold', r))
        if not touch: pg.screenshot(path=f'compat-{ENGINE}-{name}-{loc}-player.png')
        elif loc == 'ko-KR': pg.screenshot(path=f'compat-{ENGINE}-{name}-player.png')
        pg.clock.run_for(16000); pg.clock.run_for(6000); pg.clock.run_for(31000); pg.wait_for_timeout(150)
        if pg.evaluate("document.querySelector('#check').classList.contains('on')"):
            o = pg.evaluate(over)
            if o > 1: bad.append(('check', o))
            pg.click('#toResult'); pg.wait_for_timeout(100)
            o = pg.evaluate(over)
            if o > 1: bad.append(('result', o))
        else: bad.append(('no check screen', pg.evaluate("document.querySelector('.screen.on').id")))
        print(ENGINE, name, loc, 'OK' if not bad and not pe else ('BAD', bad, pe))
        if bad or pe: errs.append((name, loc, bad, pe))
        ctx.close()
print('ERR', errs)
