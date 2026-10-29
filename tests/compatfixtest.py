# 호환성 수정 확인: 제목·홈 화면 이름(7), 두 번 탭 확대 방지(5), 터치 기기 −/+ 44px(6),
# 320px 화면 보정(1), 전체 화면을 사용자가 풀면 일시정지(4)
import os
from playwright.sync_api import sync_playwright
URL = 'file://' + __import__('pathlib').Path(__file__).resolve().parent.parent.joinpath('index.html').as_posix()
errs = []
def check(cond, msg):
    if not cond: errs.append(msg)
def open_calib(pg):
    pg.click('#todayRows li:nth-child(1) button'); pg.wait_for_timeout(150)
    return pg.evaluate("document.querySelector('#calib').classList.contains('on')")
def to_player(pg):
    if pg.evaluate("document.querySelector('#dash').classList.contains('on')") and open_calib(pg): pg.click('#calibSave'); pg.wait_for_timeout(150)
    pg.click('#segTime button:nth-child(2)'); pg.click('#briefGo'); pg.clock.run_for(3500); pg.wait_for_timeout(50)
with sync_playwright() as p:
    b = getattr(p, os.environ.get('BROWSER', 'chromium')).launch()
    # 7 · 5
    pg = b.new_page(); pg.goto(URL); pg.wait_for_timeout(150)
    # 실행 전 HTML의 제목(홈 화면에 추가할 때 쓰임). 실행 뒤에는 언어에 맞게 스크립트가 바꾼다.
    html = __import__('pathlib').Path(__file__).resolve().parent.parent.joinpath('index.html').read_text()
    import re
    head = [re.search(r'<title>(.*?)</title>', html).group(1), re.search(r'apple-mobile-web-app-title" content="([^"]+)"', html).group(1)]
    print('title', head); check(head == ['속독 트레이닝', '속독 트레이닝'], f'title {head}')
    ta = pg.evaluate("getComputedStyle(document.querySelector('.pref')).touchAction"); print('button touch-action', ta)
    check(ta == 'manipulation', f'touch-action {ta}')
    check(pg.evaluate("getComputedStyle(document.querySelector('#stage')).touchAction") == 'none', 'stage touch-action changed')
    pg.close()
    # 1 · 6 · 4 (휴대폰·태블릿 크기, 한/영)
    for loc, w in [('en-US', 320), ('ko-KR', 320), ('en-US', 390), ('ko-KR', 820)]:
        ctx = b.new_context(viewport={'width': w, 'height': 900}, locale=loc, is_mobile=True, has_touch=True, device_scale_factor=2)
        pg = ctx.new_page(); pe = []; pg.on('pageerror', lambda e: pe.append(str(e)))
        pg.clock.install(); pg.goto(URL); pg.wait_for_timeout(150)
        check(open_calib(pg), 'calib not shown')
        r = pg.evaluate("""(() => { const c = document.querySelector('#cardRect'), r = c.getBoundingClientRect();
          return { over: Math.max(document.documentElement.scrollWidth, innerWidth) - %d, tall: c.classList.contains('tall'), w: Math.round(r.width), h: Math.round(r.height),
                   right: Math.round(r.right), vw: innerWidth, box: document.querySelector('.cardbox').clientWidth, label: c.innerText }; })()""" % w)
        print(loc, w, 'calib', r)
        check(r['over'] <= 1, f'{loc} {w} calib overflow {r}')
        check(r['right'] <= r['vw'], f'{loc} {w} card clipped {r}')
        check(r['tall'] == (323 > r['box'] - 4), f'{loc} {w} tall={r["tall"]} box={r["box"]}')
        if r['tall']: check(abs(r['h'] - 323) <= 1 and abs(r['w'] - 323 * 53.98 / 85.6) <= 1.5, f'tall card size {r}')
        # 보정값은 긴 변 기준 그대로 저장
        pg.click('#calibSave'); pg.wait_for_timeout(150)
        ppm = pg.evaluate("JSON.parse(localStorage.getItem('sr-proto-calib-v1')).pxPerMm")
        check(abs(ppm - 323 / 85.6) < 0.01, f'pxPerMm {ppm}')
        to_player(pg)
        pb = pg.evaluate("(() => { const r = document.querySelector('#paceUp').getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })()")
        check(pb == [44, 44], f'pace button {pb}')
        # 사용자가 전체 화면을 풀었다 (fullscreenElement 없음 + 이벤트) → 일시정지
        check(not pg.evaluate("document.querySelector('#pauseOvl').classList.contains('on')"), 'paused too early')
        # 실제 전체 화면이면 사용자처럼 빠져나오고, 엔진이 전체 화면을 주지 않았으면 이벤트만 보낸다
        pg.evaluate("document.fullscreenElement ? document.exitFullscreen() : document.dispatchEvent(new Event('fullscreenchange'))"); pg.wait_for_timeout(150)
        paused = pg.evaluate("document.querySelector('#pauseOvl').classList.contains('on')")
        print('  pace btn', pb, 'paused after fullscreen exit', paused); check(paused, 'not paused on fullscreen exit')
        pg.click('#resumeBtn'); pg.wait_for_timeout(50)
        check(not pg.evaluate("document.querySelector('#pauseOvl').classList.contains('on')"), 'resume failed')
        check(not pe, f'page errors {pe}'); ctx.close()
    # 데스크톱(마우스): −/+ 는 기존 36px 그대로
    pg = b.new_page(viewport={'width': 1440, 'height': 900}); pg.clock.install(); pg.goto(URL); pg.wait_for_timeout(150); to_player(pg)
    pb = pg.evaluate("Math.round(document.querySelector('#paceUp').getBoundingClientRect().width)"); print('desktop pace', pb)
    check(pb == 36, f'desktop pace {pb}')
    # 앱이 스스로 전체 화면을 풀 때(훈련 끝내기)는 결과 흐름 그대로
    pg.click('#pauseBtn'); pg.click('#quitBtn'); pg.wait_for_timeout(100)
    print('after quit', pg.evaluate("document.querySelector('.screen.on').id"))
print('ERR', errs)
