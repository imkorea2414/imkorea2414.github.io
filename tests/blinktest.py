from playwright.sync_api import sync_playwright
URL='file://' + __import__('pathlib').Path(__file__).resolve().parent.parent.joinpath('index.html').as_posix() + ''
with sync_playwright() as p:
    b=p.chromium.launch()
    for loc,vp in [('ko-KR',(1366,900)),('en-US',(390,844))]:
        pg=b.new_page(viewport={'width':vp[0],'height':vp[1]}, locale=loc); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.clock.install(); pg.goto(URL); pg.wait_for_timeout(200)
        pg.click('#todayRows li:nth-child(1) button'); pg.wait_for_timeout(100)
        if pg.evaluate("document.querySelector('#calib').classList.contains('on')"): pg.click('#calibSave'); pg.wait_for_timeout(150)
        print('screen brief?', pg.evaluate("document.querySelector('#brief').classList.contains('on')"), pg.evaluate("[...document.querySelectorAll('.screen.on')].map(s=>s.id)"))
        if not pg.evaluate("document.querySelector('#brief').classList.contains('on')"): print('skip'); continue
        print('segs', pg.inner_text('#segTime').replace('\n',' / '))
        print('hint', pg.inner_text('#timeHint'))
        pg.screenshot(path=f'bl-brief-{loc}.png', full_page=True)
        pg.click('#segTime button:nth-child(1)'); print('demo hint', pg.inner_text('#timeHint').split('\n')[-2:])
        pg.click('#briefGo'); pg.clock.run_for(3500); pg.clock.run_for(16000); pg.clock.run_for(6000); pg.clock.run_for(31000); pg.wait_for_timeout(200)
        print('screen', pg.evaluate("[...document.querySelectorAll('.screen.on')].map(s=>s.id)"))
        print('first hidden', pg.evaluate("document.querySelector('#blinkFirstG').hidden"))
        pg.click('#segBlink button:nth-child(3)'); print('first hidden after 3-5', pg.evaluate("document.querySelector('#blinkFirstG').hidden"))
        pg.click('#segBlinkFirst button:nth-child(2)')
        pg.screenshot(path=f'bl-check-{loc}.png', full_page=True)
        pg.click('#toResult'); print('rBlink', pg.inner_text('#rBlink'))
        print('rec', pg.evaluate("JSON.parse(localStorage.getItem('sr-proto-v1')).slice(-1)[0]"))
        # inject 2 completed day1 records -> recommend p5
        pg.evaluate("""()=>{const a=JSON.parse(localStorage.getItem('sr-proto-v1'));for(let i=0;i<2;i++)a.push({frame:'A-I',preset:'day1',aborted:false,trainSec:180,date:'2026-10-20',ts:Date.now()});localStorage.setItem('sr-proto-v1',JSON.stringify(a))}""")
        pg.click('#backBtn'); pg.click('#todayRows li:nth-child(1) button'); pg.wait_for_timeout(100)
        print('segs after', pg.inner_text('#segTime').replace('\n',' / '))
        print('ERRORS', errs); pg.close()
