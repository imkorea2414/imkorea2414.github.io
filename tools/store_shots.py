"""Play 스토어용 그래픽 이미지와 스크린샷을 만든다 (예시 기록을 넣은 화면).
사용 (저장소 루트): python3 tools/build.py && python3 tools/store_shots.py
결과: docs/store/*.png
"""
import pathlib, datetime, random, json
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs/store'
OUT.mkdir(parents=True, exist_ok=True)
URL = (ROOT / 'index.html').as_uri()

# 예시 기록: Day 12까지 진행, 1분 측정 10회, 시각능력 측정 몇 회 (화면 설명용 가상 데이터)
def seed():
    rnd = random.Random(7)
    today = datetime.date.today()
    ds = lambda k: (lambda d: f'{d.year}-{d.month}-{d.day}')(today - datetime.timedelta(days=k))
    trains, meas = [], []
    for i, k in enumerate(range(11, -1, -1)):
        for fr, sec in [('A-I', 300), ('B-I', 60), ('C-I-1', 90)]:
            trains.append({'date': ds(k), 'ts': i * 1000, 'frame': fr, 'trainSec': sec, 'rounds': 1, 'roundsTotal': 1, 'passes': 40 + i * 3,
                           'pace': 1, 'accuracy': 90, 'aborted': False, 'reactions': ['tears'] if i % 3 == 0 else ['none'], 'preset': 'plan',
                           'turns': 0, 'turnAvgMs': None, 'parts': None, 'partStat': None,
                           'blinks': {'count': ['0', '1-2', '3-5'][i % 3], 'first': 'mid'}})
        if i >= 6:
            trains.append({'date': ds(k), 'ts': i * 1000 + 1, 'frame': 'D-CHK', 'trainSec': 60, 'passes': 520 + (i - 6) * 70 + rnd.randint(-20, 20),
                           'aborted': False, 'preset': 'plan'})
        if i % 1 == 0 and i < 10:
            sp = 820 + i * 55 + rnd.randint(-30, 30); comp = 67 if i % 2 else 100
            meas.append({'date': ds(k + 2 if k < 10 else k), 'ts': i * 1000 + 2, 'lang': 'ko', 'unit': 'chars', 'passage': 'ko-lighthouse', 'mode': 'normal',
                         'elapsed': 60, 'count': sp, 'speed': sp, 'self9': 7, 'correct': 2 if i % 2 else 3, 'total': 3, 'comp': comp, 'rei': round(sp * comp / 100)})
    done = {str(d): True for d in range(1, 12)}
    return {'sr-proto-v1': trains, 'sr-proto-meas-v1': meas, 'sr-proto-prog-v1': {'day': 12, 'done': done},
            'sr-proto-calib-v1': {'pxPerMm': 3.78, 'distance': 40, 'aDiam': 6, 'aGap': 11.8, 'bDiam': 7, 'bSpan': 251}}

NAV = "l => [...document.querySelectorAll('#tabbar button, .nav button')].find(b => b.offsetParent && b.textContent == l).click()"

def open_ctx(b, w, h, dpr):
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=dpr, locale='ko-KR', color_scheme='light',
                        is_mobile=w < 1000, has_touch=True)
    pg = ctx.new_page()
    pg.add_init_script("(s => { if (!sessionStorage.getItem('seeded')) { localStorage.clear(); for (const k in s) localStorage.setItem(k, JSON.stringify(s[k])); sessionStorage.setItem('seeded', '1'); } })(" + json.dumps(seed()) + ")")
    pg.clock.install(); pg.goto(URL); pg.wait_for_timeout(400)
    return ctx, pg

def training(pg):
    # 제2단계 두 쪽 펼침, 도입이 끝나고 눈으로만 따라가는 훈련 단계까지 진행
    pg.evaluate(NAV, 'Training'); pg.wait_for_timeout(150)
    pg.click("#trList button:has-text('C-I-1')"); pg.wait_for_timeout(200)
    pg.click('#segTime button:nth-child(2)'); pg.click('#briefGo')
    pg.clock.run_for(3500)
    for _ in range(120):  # 도입이 끝나고 훈련 전 카운트다운이 다시 뜰 때까지
        pg.clock.run_for(500)
        if pg.evaluate("document.querySelector('#cdOvl').classList.contains('on')"): break
    pg.clock.run_for(3500); pg.clock.run_for(5000)

def shots(b, prefix, w, h, dpr):
    ctx, pg = open_ctx(b, w, h, dpr)
    n = 0
    def snap(name):
        nonlocal n; n += 1
        pg.wait_for_timeout(150); pg.screenshot(path=str(OUT / f'{prefix}-{n}-{name}.png'))
    snap('dashboard')
    if prefix == 'phone':
        # 휴대폰 세로에서는 훈련 틀이 작아 가로 화면(1920×1080)으로 따로 찍는다
        n += 1
        c2, p2 = open_ctx(b, h, w, dpr); training(p2); p2.wait_for_timeout(150)
        p2.screenshot(path=str(OUT / f'{prefix}-{n}-training-landscape.png')); c2.close()
    else:
        training(pg); snap('training')
        pg.goto(URL); pg.wait_for_timeout(300)
    # 1분 측정 읽기 화면
    pg.evaluate(NAV, 'Test'); pg.wait_for_timeout(150)
    pg.click('#teList li:nth-child(1) button'); pg.wait_for_timeout(200)
    if pg.is_visible('#briefGo'): pg.click('#briefGo'); pg.clock.run_for(3500); pg.clock.run_for(15000)
    snap('measure')
    pg.goto(URL); pg.wait_for_timeout(300)
    pg.evaluate(NAV, 'Progress'); snap('progress')
    pg.evaluate(NAV, 'Curriculum'); snap('curriculum')
    ctx.close()

FEATURE = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@500;600&display=swap" rel="stylesheet">
<style>
html,body{margin:0;width:1024px;height:500px;background:#F4F5F6;font-family:"IBM Plex Sans KR",sans-serif;color:#14171A;overflow:hidden}
.w{position:absolute;inset:0;padding:72px 80px;display:flex;flex-direction:column;justify-content:space-between}
h1{font-size:76px;line-height:1;margin:0;letter-spacing:-.03em;font-weight:600}
p{font-size:26px;color:#656B72;margin:18px 0 0}
.row{display:flex;gap:26px;align-items:center}
.c{width:30px;height:30px;border-radius:50%;border:3px solid #14171A;box-sizing:border-box}
.c.on{background:#2348F5;border-color:#2348F5;box-shadow:0 0 0 10px rgba(35,72,245,.14)}
.k{font-size:18px;color:#656B72;letter-spacing:.08em}
</style></head><body><div class="w">
<div><h1>속독 트레이닝</h1><p>48일 훈련 과정 · 화면 보정 · 1분 독서 측정</p></div>
<div><div class="row">""" + ''.join(f'<i class="c{" on" if i == 5 else ""}"></i>' for i in range(13)) + """</div>
<div class="k" style="margin-top:28px">SPEED READING TRAINING</div></div>
</div></body></html>"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1024, 'height': 500})
    pg.set_content(FEATURE); pg.wait_for_timeout(800); pg.screenshot(path=str(OUT / 'feature-1024x500.png')); pg.close()
    shots(b, 'phone', 360, 640, 3)        # 1080×1920
    shots(b, 'tablet7', 600, 960, 2)      # 1200×1920
    shots(b, 'tablet10', 1280, 800, 2)    # 2560×1600
    b.close()
print('saved to', OUT)
