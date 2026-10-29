# Training·Test 메뉴: 탭이 열리고, 모든 훈련이 단계별로 보이며, 눌러서 훈련·측정으로 들어가는지
import os
from playwright.sync_api import sync_playwright
URL = 'file://' + __import__('pathlib').Path(__file__).resolve().parent.parent.joinpath('index.html').as_posix()
NAV = "l => [...document.querySelectorAll('#tabbar button, .nav button')].find(b => b.offsetParent && b.textContent == l).click()"
errs = []
def check(c, m):
    if not c: errs.append(m)
with sync_playwright() as p:
    b = getattr(p, os.environ.get('BROWSER', 'chromium')).launch()
    for loc, vp, mob in [('ko-KR', (390, 844), True), ('en-US', (1366, 900), False)]:
        pg = b.new_page(viewport={'width': vp[0], 'height': vp[1]}, locale=loc, is_mobile=mob, has_touch=mob)
        pe = []; pg.on('pageerror', lambda e: pe.append(str(e)))
        pg.clock.install(); pg.goto(URL); pg.wait_for_timeout(200)
        pg.evaluate("localStorage.setItem('sr-proto-calib-v1', JSON.stringify({pxPerMm: 3.78, distance: 50, aDiam: 6, aGap: 11.8, bDiam: 7, bSpan: 251}))"); pg.reload(); pg.wait_for_timeout(200)
        disabled = pg.evaluate("[...document.querySelectorAll('#tabbar [aria-disabled], .nav [aria-disabled]')].length")
        check(disabled == 0, f'disabled nav items {disabled}')
        pg.evaluate(NAV, 'Training'); pg.wait_for_timeout(150)
        check(pg.evaluate("document.querySelector('#train').classList.contains('on')"), 'training screen not shown')
        groups = pg.eval_on_selector_all('#trList .trg h2', 'l => l.map(x => x.textContent)')
        names = pg.eval_on_selector_all('#trList .nm', 'l => l.map(x => x.firstChild.textContent)')
        tags = pg.eval_on_selector_all('#trList .nm .tag', 'l => l.map(x => x.textContent)')
        st = pg.eval_on_selector_all('#trList .st', 'l => l.map(x => x.textContent)')
        print(loc, groups, len(names), 'rows'); print('  ', names[:4], tags[:4], st[:4])
        check(len(groups) == 5 and len(names) == 19, f'groups {len(groups)} rows {len(names)}')
        check(len(tags) == len(names) and all(t.startswith(('원전 p.', 'Source p.')) for t in tags), f'tags {tags}')
        check(all(s for s in st), 'missing course day')
        over = pg.evaluate("Math.max(document.documentElement.scrollWidth, innerWidth) - %d" % vp[0]); check(over <= 1, f'train overflow {over}')
        # 하나 열기 → 훈련 전 안내
        pg.click("#trList button:has-text('B-II')"); pg.wait_for_timeout(150)
        check(pg.evaluate("document.querySelector('#brief').classList.contains('on')"), 'B-II brief not opened')
        pg.go_back(); pg.wait_for_timeout(150)
        pg.evaluate(NAV, 'Test'); pg.wait_for_timeout(150)
        rows = pg.eval_on_selector_all('#teList .nm', 'l => l.map(x => x.textContent)'); print('  test rows', rows)
        check(len(rows) == 2, f'test rows {rows}')
        over = pg.evaluate("Math.max(document.documentElement.scrollWidth, innerWidth) - %d" % vp[0]); check(over <= 1, f'test overflow {over}')
        pg.click('#teList li:nth-child(1) button'); pg.wait_for_timeout(150)
        on = pg.evaluate("document.querySelector('.screen.on').id"); print('  measure ->', on)
        check(on in ('brief', 'mread'), f'measure opened {on}')
        # 탭에서 현재 화면 표시
        pg.go_back(); pg.wait_for_timeout(150); pg.evaluate(NAV, 'Training'); pg.wait_for_timeout(100)
        cur = pg.eval_on_selector_all('[aria-current=page]', 'l => l.filter(x => x.offsetParent).map(x => x.textContent)')
        check('Training' in cur, f'aria-current {cur}')
        check(not pe, f'page errors {pe}'); pg.close()
print('ERR', errs)
