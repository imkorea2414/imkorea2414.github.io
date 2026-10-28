from playwright.sync_api import sync_playwright
URL='file://' + __import__('pathlib').Path(__file__).resolve().parent.parent.joinpath('index.html').as_posix() + ''
IDS=['C-I-1','C-I-2','C-II-1','C-II-2','C-III','C-IV']
with sync_playwright() as p:
    b=getattr(p, __import__("os").environ.get("BROWSER", "chromium")).launch()
    pg=b.new_page(viewport={'width':1440,'height':900}, locale='ko-KR'); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.clock.install(); pg.goto(URL); pg.wait_for_timeout(200)
    pg.screenshot(path='c-dash.png', full_page=True)
    print('s2 rows', pg.eval_on_selector_all('#s2Rows li','l=>l.map(x=>x.innerText.replace(/\\n/g," | "))'))
    # regression A-I demo
    pg.click('#todayRows li:nth-child(1) button'); pg.wait_for_timeout(100)
    if pg.evaluate("document.querySelector('#calib').classList.contains('on')"): pg.click('#calibSave'); pg.wait_for_timeout(150)
    pg.click('#segTime button:has-text("체험")'); pg.click('#briefGo'); pg.clock.run_for(3200); pg.clock.run_for(16000); pg.clock.run_for(3200); pg.clock.run_for(31000); pg.wait_for_timeout(100)
    print('A-I ->', pg.evaluate("[...document.querySelectorAll('.screen.on')].map(s=>s.id)"))
    pg.click('#toResult'); print('A-I passes', pg.inner_text('#rPasses'))
    pg.click('#backBtn')
    for k,id in enumerate(IDS):
        pg.click(f'#s2Rows li:nth-child({k+5}) button'); pg.wait_for_timeout(100)
        pg.click('#segTime button:nth-child(1)')
        if k==0: pg.screenshot(path='c-brief.png', full_page=True)
        if id=='C-III': pg.screenshot(path='c-brief3.png', full_page=True)
        pg.click('#briefGo'); pg.clock.run_for(3200); pg.wait_for_timeout(50)
        # intro: tap the highlighted circle each beat for 3 beats
        for t in range(3):
            pos=pg.evaluate("(()=>{const c=document.querySelector('#stage .c.on');if(!c)return null;const r=c.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()")
            if pos: pg.mouse.click(pos[0],pos[1])
            pg.clock.run_for(1000); pg.wait_for_timeout(20)
        pg.screenshot(path=f'c-{id}-intro.png')
        # training
        pg.clock.run_for(8000); pg.wait_for_timeout(50)
        turns=0
        for t in range(40):
            st=pg.evaluate("document.querySelector('#phaseLabel').innerText")
            if '책장' in st:
                if turns==0: pg.screenshot(path=f'c-{id}-turn.png')
                pg.clock.run_for(700); pg.keyboard.press('ArrowRight'); turns+=1
            pg.clock.run_for(1000)
            if not pg.evaluate("document.querySelector('#player').classList.contains('on')"): break
        if id=='C-IV': pg.screenshot(path='c-C-IV-train.png')
        for t in range(150):
            if not pg.evaluate("document.querySelector('#player').classList.contains('on')"): break
            st=pg.evaluate("document.querySelector('#phaseLabel').innerText")
            if '책장' in st: pg.keyboard.press('ArrowRight'); turns+=1
            pg.clock.run_for(1000)
        print(id, 'screen', pg.evaluate("[...document.querySelectorAll('.screen.on')].map(s=>s.id)"), 'turns pressed', turns)
        pg.click('#toResult'); pg.wait_for_timeout(50)
        print('  result passes', pg.inner_text('#rPasses'), '| turn', pg.inner_text('#rTurn') if pg.is_visible('#rTurnRow') else '-', '| part', pg.inner_text('#rPart') if pg.is_visible('#rPartRow') else '-', '| next', pg.inner_text('#nextBtn'))
        if id=='C-III': pg.screenshot(path='c-result3.png', full_page=True)
        pg.click('#backBtn'); pg.wait_for_timeout(50)
    print('ERRORS', errs)
