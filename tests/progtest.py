from playwright.sync_api import sync_playwright
import json, random
URL='file://' + __import__('pathlib').Path(__file__).resolve().parent.parent.joinpath('index.html').as_posix() + ''
random.seed(3)
T=[];M=[]
for i in range(12):
    d=f'2026-10-{12+i}'
    T.append({'date':d,'frame':'A-I','trainSec':180+i*30,'reactions':random.sample(['tears','sting','head','blur'],2),'blinks':{'count':random.choice(['0','1-2','3-5']),'first':'mid'}})
    if i>=4: T.append({'date':d,'frame':'D-CHK','trainSec':60,'passes':300+i*70+random.randint(-30,30),'aborted':False,'reactions':[]})
    M.append({'date':d,'lang':'ko','unit':'chars','speed':480+i*55+random.randint(-40,40),'comp':random.choice([67,100,67,33,100]),'rei':None,'elapsed':60})
for m in M: m['rei']=round(m['speed']*m['comp']/100)
with sync_playwright() as p:
    b=getattr(p, __import__("os").environ.get("BROWSER", "chromium")).launch()
    for name,vp,cs in [('desk',(1280,900),'light'),('phone',(390,844),'dark')]:
        pg=b.new_page(viewport={'width':vp[0],'height':vp[1]}, locale='ko-KR', color_scheme=cs); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(URL); pg.evaluate(f"localStorage.setItem('sr-proto-v1', {json.dumps(json.dumps(T))}); localStorage.setItem('sr-proto-meas-v1', {json.dumps(json.dumps(M))}); localStorage.setItem('sr-proto-prog-v1', JSON.stringify({{day:13, done:{{1:'2026-10-12',2:'2026-10-13',3:'2026-10-14'}}}}))")
        pg.reload(); pg.wait_for_timeout(200)
        if name=='desk': pg.click('.nav button:has-text("Progress")')
        else: pg.click('#tabbar button:has-text("Progress")')
        pg.wait_for_timeout(200); pg.screenshot(path=f'prog-{name}.png', full_page=True)
        print(name, pg.inner_text('#pgStats').replace('\n',' '), 'ERR', errs); pg.close()
