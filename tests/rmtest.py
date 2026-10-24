from playwright.sync_api import sync_playwright
URL='file://' + __import__('pathlib').Path(__file__).resolve().parent.parent.joinpath('index.html').as_posix() + ''
with sync_playwright() as p:
    b=p.chromium.launch()
    for vp,loc in [((1440,900),'ko-KR'),((1180,820),'en-US')]:
        pg=b.new_page(viewport={'width':vp[0],'height':vp[1]}, locale=loc); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.clock.install(); pg.goto(URL); pg.wait_for_timeout(200)
        names=pg.eval_on_selector_all('#s2Rows li .nm','l=>l.map(x=>x.innerText)'); i=len(names)
        pg.click(f'#s2Rows li:nth-child({i}) button'); pg.wait_for_timeout(100)
        if pg.evaluate("document.querySelector('#calib').classList.contains('on')"): pg.click('#calibSave'); pg.wait_for_timeout(150)
        print('brief', pg.inner_text('#bTitle'))
        pg.click('#segTime button:nth-child(1)'); pg.click('#briefGo'); pg.wait_for_timeout(200); pg.clock.run_for(3200); pg.wait_for_timeout(50)
        print('segs', pg.evaluate("RMS? RMS.segs.length : 'n/a'") if False else '')
        pg.clock.run_for(4000); pg.wait_for_timeout(50); pg.screenshot(path=f'rm-intro-{loc}.png')
        pg.clock.run_for(6500); pg.clock.run_for(3200); pg.clock.run_for(5000); pg.wait_for_timeout(50)
        print('phase', pg.inner_text('#rmPhase'), '| pace', pg.inner_text('#rmPace'))
        pg.screenshot(path=f'rm-train-{loc}.png')
        for k in range(5): pg.keyboard.press('ArrowUp')
        for t in range(40):
            if not pg.evaluate("document.querySelector('#rm').classList.contains('on')"): break
            if '넘기기' in pg.inner_text('#rmPhase') or 'Turn' in pg.inner_text('#rmPhase'):
                pg.screenshot(path=f'rm-turn-{loc}.png'); pg.keyboard.press('ArrowRight')
            pg.clock.run_for(1000)
        print('screen', pg.evaluate("document.querySelector('.screen.on').id"))
        pg.click('#toResult'); print('result', pg.inner_text('#rPasses'), pg.inner_text('#rPace'), pg.inner_text('#rTurn') if pg.is_visible('#rTurnRow') else '')
        print('ERR', errs); pg.close()
