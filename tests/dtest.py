from playwright.sync_api import sync_playwright
URL='file://' + __import__('pathlib').Path(__file__).resolve().parent.parent.joinpath('index.html').as_posix() + ''
def open_extra(pg, name):
    names=pg.eval_on_selector_all('#s2Rows li .nm','l=>l.map(x=>x.innerText)')
    i=names.index(name); pg.click(f'#s2Rows li:nth-child({i+1}) button'); pg.wait_for_timeout(100)
    if pg.evaluate("document.querySelector('#calib').classList.contains('on')"): pg.click('#calibSave'); pg.wait_for_timeout(150)
with sync_playwright() as p:
    b=getattr(p, __import__("os").environ.get("BROWSER", "chromium")).launch(); pg=b.new_page(viewport={'width':1440,'height':900}, locale='ko-KR'); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.clock.install(); pg.goto(URL); pg.wait_for_timeout(200)
    open_extra(pg,'제3단계 D-I-1'); pg.screenshot(path='d-brief.png', full_page=True)
    pg.click('#briefGo'); pg.clock.run_for(3200)
    for t in range(12):
        pos=pg.evaluate("(()=>{const c=document.querySelector('#stage .c.on');if(!c)return null;const r=c.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()")
        if pos: pg.mouse.click(*pos)
        pg.clock.run_for(500)
    pg.screenshot(path='d-I1-intro.png')
    pg.clock.run_for(30000); pg.clock.run_for(3200); pg.clock.run_for(8000); pg.wait_for_timeout(50)
    pg.keyboard.press('ArrowUp'); pg.keyboard.press('ArrowUp'); print('pace', pg.inner_text('#hPace'))
    pg.clock.run_for(60000); pg.wait_for_timeout(50)
    print('screen', pg.evaluate("document.querySelector('.screen.on').id")); pg.click('#toResult')
    print('result passes', pg.inner_text('#rPasses'), 'acc', pg.inner_text('#rAcc'), 'pace', pg.inner_text('#rPace'))
    pg.click('#backBtn')
    open_extra(pg,'제3단계 D-II-1'); pg.click('#segTime button:nth-child(1)'); pg.click('#briefGo'); pg.clock.run_for(3200); pg.clock.run_for(10000); pg.clock.run_for(3200); pg.clock.run_for(12000); pg.wait_for_timeout(50)
    pg.screenshot(path='d-II1-train.png')
    pg.click('#pauseBtn'); pg.click('#quitBtn'); pg.click('#toResult'); pg.click('#backBtn')
    # D-CHK
    open_extra(pg,'시각능력 1분 측정'); pg.screenshot(path='d-chk-brief.png', full_page=True)
    pg.click('#briefGo'); pg.clock.run_for(3200); pg.clock.run_for(30000)
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(50)
    pg.clock.run_for(31000); pg.wait_for_timeout(100)
    print('phase', pg.inner_text('#phaseLabel'))
    # click 3rd circle of row 2 on spread 2 left page
    c=pg.evaluate("(()=>{const cs=[...document.querySelectorAll('#stage .c')];const r=cs[12].getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()")
    pg.mouse.click(*c); pg.wait_for_timeout(50); print('sel', pg.inner_text('#phaseLabel'))
    pg.screenshot(path='d-chk-mark.png')
    pg.click('#markOk'); pg.wait_for_timeout(50); pg.click('#toResult')
    print('chk passes', pg.inner_text('#rPasses'), '|', pg.inner_text('#rBest'), '| label', pg.inner_text('#rPassL'))
    print('ERR', errs)
