from playwright.sync_api import sync_playwright
import json
URL='file://' + __import__('pathlib').Path(__file__).resolve().parent.parent.joinpath('index.html').as_posix() + ''
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':900}, locale='ko-KR'); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(200)
    print('day', pg.inner_text('#dayNum'), '|', pg.inner_text('#lvlNum'), pg.inner_text('#lvlName'))
    print('rows', pg.eval_on_selector_all('#todayRows li','l=>l.map(x=>x.innerText.replace(/\\n/g," | "))'))
    print('est', pg.inner_text('#todayEst'))
    for d in [4,9,15,21,22,30,37,48]:
        pg.evaluate(f"localStorage.setItem('sr-proto-prog-v1', JSON.stringify({{day:{d}, done:{{}}}}))"); pg.reload(); pg.wait_for_timeout(150)
        print(d, pg.inner_text('#lvlNum'), '|', pg.eval_on_selector_all('#todayRows li','l=>l.map(x=>x.innerText.split("\\n").slice(0,2).join(" "))'), pg.inner_text('#todayEst'))
    # brief from plan
    pg.evaluate("localStorage.setItem('sr-proto-prog-v1', JSON.stringify({day:10, done:{}}))"); pg.reload(); pg.wait_for_timeout(150)
    pg.click('#todayRows li:nth-child(1) button'); pg.wait_for_timeout(100)
    if pg.evaluate("document.querySelector('#calib').classList.contains('on')"): pg.click('#calibSave'); pg.wait_for_timeout(150)
    print('brief seg', pg.inner_text('#segTime').replace('\n',' / '), '| hint', pg.inner_text('#timeHint').split('\n')[0][:120])
    print('ERR', errs)
