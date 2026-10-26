# 화면 켜짐 잠금: 훈련 중 앱이 뒤로 갔다 돌아오면 다시 요청하는지, 훈련이 끝나면 풀리는지 확인
from playwright.sync_api import sync_playwright
URL='file://' + __import__('pathlib').Path(__file__).resolve().parent.parent.joinpath('index.html').as_posix()
MOCK = """
window.__wl = { req: 0, live: 0 };
Object.defineProperty(navigator, 'wakeLock', { value: { request: async () => {
  __wl.req++; __wl.live++;
  const s = { released: false, release: async () => { if (!s.released){ s.released = true; __wl.live--; } } };
  window.__wlLast = s; return s; } } });
Object.defineProperty(document, 'visibilityState', { get: () => window.__vis || 'visible' });
Object.defineProperty(document, 'hidden', { get: () => (window.__vis || 'visible') === 'hidden' });
"""
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1366,'height':900}, locale='ko-KR'); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script(MOCK); pg.clock.install(); pg.goto(URL); pg.wait_for_timeout(200)
    pg.click('#todayRows li:nth-child(1) button'); pg.wait_for_timeout(100)
    if pg.evaluate("document.querySelector('#calib').classList.contains('on')"): pg.click('#calibSave'); pg.wait_for_timeout(150)
    pg.click('#segTime button:nth-child(2)'); pg.click('#briefGo'); pg.clock.run_for(3500); pg.wait_for_timeout(50)
    print('start', pg.evaluate('__wl'))
    # 앱이 뒤로 감: 브라우저가 잠금을 풂 → 일시정지
    pg.evaluate("window.__vis='hidden'; __wlLast.release(); document.dispatchEvent(new Event('visibilitychange'))"); pg.wait_for_timeout(50)
    print('hidden', pg.evaluate('__wl'), 'paused', pg.evaluate("document.querySelector('#pauseOvl').classList.contains('on')"))
    pg.evaluate("window.__vis='visible'; document.dispatchEvent(new Event('visibilitychange'))"); pg.wait_for_timeout(50)
    back = pg.evaluate('__wl'); print('visible again', back)
    pg.click('#quitBtn'); pg.wait_for_timeout(100)
    end = pg.evaluate('__wl'); print('after quit', end)
    # 훈련 밖에서는 다시 요청하지 않아야 한다
    pg.evaluate("window.__vis='visible'; document.dispatchEvent(new Event('visibilitychange'))"); pg.wait_for_timeout(50)
    idle = pg.evaluate('__wl'); print('outside training', idle)
    ok = back['req']==2 and back['live']==1 and end['live']==0 and idle['req']==2
    if not ok: errs.append('wake lock behaviour wrong')
    print('ERR', errs)
