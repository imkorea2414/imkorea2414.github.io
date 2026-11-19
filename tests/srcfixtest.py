# 원전 검증(2026-11-19) 뒤 수정 확인:
#  - A-III에는 인용문이 없다 (원전 p.54~55), A-I·A-II에는 있다
#  - 단계 조건 → "참고 목표". 원전 근거 없는 1,500·2,400 표시 없음, 1,200은 p.154
#  - 정리 시간(원전 "정리 및 상담활동") 설명, 상담을 제공한다는 표현 없음
#  - 사방훈련: 48일 계획에서 4곳 + 가장 어려웠던 곳 1회 (원전 p.73·111), 적용 과정(37~48일)에는 배정하지 않음
#  - 원전 모형별 표보다 길게 배정된 날 안내
#  - R.E.I. = 속도 × 9점 척도 × 0.1 (원전 p.32), 문항 정답률은 따로, 이전 방식 기록은 * 로 구분하고 값은 그대로
import os, json, re
from playwright.sync_api import sync_playwright
URL = 'file://' + __import__('pathlib').Path(__file__).resolve().parent.parent.joinpath('index.html').as_posix()
ENGINE = os.environ.get('BROWSER', 'chromium')
NAV = "l => [...document.querySelectorAll('#tabbar button, .nav button')].find(b => b.offsetParent && b.textContent == l).click()"
CAL = {'pxPerMm': 3.9, 'distance': 40}
OLD = {'date': '2026-11-01', 'ts': 1, 'lang': 'ko', 'unit': 'chars', 'passage': 'ko-lighthouse', 'mode': 'normal', 'elapsed': 60,
       'count': 900, 'speed': 900, 'self9': 7, 'correct': 2, 'total': 3, 'comp': 67, 'rei': 603}   # 이전 방식: 900 × 67%
errs = []
def check(c, m):
    if not c: errs.append(m)

def ctx_page(b, loc='ko-KR', day=None, meas=None):
    ctx = b.new_context(viewport={'width': 1280, 'height': 900}, locale=loc)
    pg = ctx.new_page(); pe = []; pg.on('pageerror', lambda e: pe.append(str(e)))
    seed = {'sr-proto-calib-v1': CAL}
    if day: seed['sr-proto-prog-v1'] = {'day': day, 'done': {}}
    if meas is not None: seed['sr-proto-meas-v1'] = meas
    pg.add_init_script("(s => { if (!sessionStorage.getItem('seeded')) { localStorage.clear(); for (const k in s) localStorage.setItem(k, JSON.stringify(s[k])); sessionStorage.setItem('seeded', '1'); } })(" + json.dumps(seed) + ")")
    pg.clock.install(); pg.goto(URL); pg.wait_for_timeout(250)
    return ctx, pg, pe

def open_row(pg, text):
    pg.locator('#todayRows li button', has_text=text).first.click(); pg.wait_for_timeout(200)
    if pg.evaluate("document.querySelector('#calib').classList.contains('on')"): pg.click('#calibSave'); pg.wait_for_timeout(200)

with sync_playwright() as p:
    b = getattr(p, ENGINE).launch()

    # 1. 인용문
    for loc in ['ko-KR', 'en-US']:
        ctx, pg, pe = ctx_page(b, loc)
        q = {}
        for did in ['A-I', 'A-II', 'A-III']:
            pg.goto(URL); pg.wait_for_timeout(150); pg.evaluate(NAV, 'Training'); pg.wait_for_timeout(100)
            pg.locator('#trList button', has_text=re.compile(did + r'(?![I-])')).first.click(); pg.wait_for_timeout(200)
            q[did] = pg.evaluate("document.querySelectorAll('#brief li.quote').length")
        print(loc, 'quotes', q)
        check(q == {'A-I': 1, 'A-II': 1, 'A-III': 0}, f'{loc} quotes {q}')
        check(not pe, f'{loc} page errors {pe}'); ctx.close()

    # 2. 커리큘럼: 참고 목표, 정리 시간
    for loc in ['ko-KR', 'en-US']:
        ctx, pg, pe = ctx_page(b, loc)
        pg.evaluate(NAV, 'Curriculum'); pg.wait_for_timeout(150)
        pg.evaluate("document.querySelectorAll('#cuLevels details').forEach(d => d.open = true)")
        t = pg.inner_text('#curr')
        ko = loc == 'ko-KR'
        check(('참고 목표' if ko else 'Reference goal') in t, f'{loc} no reference goal label')
        check(('다음 단계 조건' if ko else 'To move up') not in t, f'{loc} old gate label still shown')
        check(not re.search(r'1,500|2,400', t), f'{loc} 1,500/2,400 still shown')
        check('1,200' in t and 'p.154' in t, f'{loc} 1,200 p.154 missing')
        check(('진행 조건이 아닙니다' if ko else 'not requirements') in t, f'{loc} reference-goal note missing')
        check(('정리 시간' if ko else 'Wrap-up') in t and ('상담을 제공하지 않습니다' if ko else 'does not offer counseling') in t, f'{loc} wrap-up note missing')
        check(not pe, f'{loc} page errors {pe}'); ctx.close()

    # 3. 사방훈련: Day 8 (초기 과정)에 C-III → 4곳 + 1, 원전 표 기준 시간, 단계 시간보다 길다는 안내
    ctx, pg, pe = ctx_page(b, 'ko-KR', day=8)
    rows = pg.inner_text('#todayRows'); print('day 8 rows:', rows.replace('\n', ' | ')[:300])
    check('C-III' in rows and '4곳 + 가장 어려웠던 곳 1회' in rows, f'C-III plan row {rows[:200]}')
    open_row(pg, 'C-III')
    hint = pg.inner_text('#timeHint'); print('C-III hint:', hint.replace('\n', ' ')[:300])
    check('4곳 + 1' in pg.inner_text('#segTime'), 'plan label 4곳 + 1 missing')
    check('훈련 합계 5:00' in hint and '보다 깁니다' in hint, 'III longer-than-stage note missing')
    check('× 4곳 + 1' in pg.inner_text('#sumRounds'), 'sumRounds not 4+1')
    pg.click('#briefGo')
    seen = []
    for _ in range(140):
        pg.clock.run_for(5000); pg.wait_for_timeout(10)
        if pg.evaluate("document.querySelector('#check').classList.contains('on')"): break
        lab = pg.evaluate("(document.querySelector('#phaseLabel') || {}).textContent || ''")
        m = re.search(r'III-(\d) \((\d)/(\d)\)', lab)
        if m and (not seen or seen[-1] != m.groups()): seen.append(m.groups())
    if pg.evaluate("document.querySelector('#check').classList.contains('on')"): pg.click('#toResult'); pg.wait_for_timeout(200)   # 기록은 결과 화면으로 넘어갈 때 저장된다
    rec = pg.evaluate("JSON.parse(localStorage.getItem('sr-proto-v1') || '[]').slice(-1)[0] || null")
    print('C-III visited:', seen, '| record parts:', rec and rec.get('parts'))
    check(rec and rec.get('parts') and len(rec['parts']) == 5 and rec['parts'][:4] == [1, 2, 3, 4], f'C-III parts {rec and rec.get("parts")}')
    check(seen and seen[-1][2] == '5', f'C-III did not reach 5 parts {seen}')
    check(not pe, f'C-III page errors {pe}'); ctx.close()

    # 4. 원전 모형별 표보다 길게 배정된 날: Day 16의 C-I-1 (원전 1분)
    ctx, pg, pe = ctx_page(b, 'ko-KR', day=16)
    open_row(pg, 'C-I-1')
    hint = pg.inner_text('#timeHint')
    check('원전 모형별 표(p.66)보다 긴 시간입니다' in hint and '과정별 시간전략' in hint, f'longer note missing: {hint[:200]}')
    ctx.close()
    ctx, pg, pe = ctx_page(b, 'en-US', day=16)
    open_row(pg, 'C-I-1')
    check('Longer than the source' in pg.inner_text('#timeHint'), 'longer note (en) missing')
    ctx.close()

    # 5. 적용 과정(Day 37~48)에는 사방훈련 없음
    bad = []
    for d in range(37, 49):
        ctx, pg, pe = ctx_page(b, 'ko-KR', day=d)
        rows = pg.inner_text('#todayRows')
        if 'C-III' in rows or 'D-III' in rows: bad.append(d)
        ctx.close()
    check(not bad, f'four-corner in application stage days {bad}')

    # 6. R.E.I.: 원전 방식, 문항 정답률 따로, 이전 기록 구분
    for loc in ['ko-KR', 'en-US']:
        ctx, pg, pe = ctx_page(b, loc, meas=[OLD])
        pg.evaluate(NAV, 'Test'); pg.wait_for_timeout(120)
        pg.click('#teList li:nth-child(1) button'); pg.wait_for_timeout(200)
        if pg.evaluate("document.querySelector('#brief').classList.contains('on')"): pg.click('#briefGo'); pg.wait_for_timeout(150)
        pg.clock.run_for(4000); pg.clock.run_for(61000); pg.wait_for_timeout(200)
        # 지금 쪽에 실제로 보이는(다른 요소에 가려지지 않은) 낱말 가운데 뒤쪽 것을 누른다
        pt = pg.evaluate("(() => { const ws = [...document.querySelectorAll('#reader .w')].filter(w => { const r = w.getBoundingClientRect(); const x = r.left + r.width / 2, y = r.top + r.height / 2;"
                         " return r.width > 0 && x > 0 && y > 0 && x < innerWidth && y < innerHeight && document.elementFromPoint(x, y) === w; });"
                         " const w = ws[Math.floor(ws.length * 0.8)]; const r = w.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
        pg.mouse.click(pt[0], pt[1]); pg.wait_for_timeout(100); pg.click('#markOk'); pg.wait_for_timeout(200)
        pg.locator('#scale9 button', has_text=re.compile(r'^4$')).click()
        for fs in pg.query_selector_all('#mcqs fieldset'): fs.query_selector('.opts button').click()
        pg.click('#qSubmit'); pg.wait_for_timeout(200)
        speed = int(re.sub(r'\D', '', pg.inner_text('#mrSpeed').split('\n')[0].split('<')[0]) or 0)
        rec = pg.evaluate("JSON.parse(localStorage.getItem('sr-proto-meas-v1')).slice(-1)[0]")
        shown = pg.inner_text('#mrRei')
        check(rec['comp'] is not None, f'{loc} no questions were asked (read too little)')
        print(loc, 'speed', rec['speed'], 'self9', rec['self9'], 'comp', rec['comp'], 'rei', rec['rei'], 'shown', shown, 'reiV', rec.get('reiV'))
        check(rec['self9'] == 4 and rec['reiV'] == 2 and abs(rec['rei'] - round(rec['speed'] * 4) / 10) < 1e-9, f'{loc} new rei {rec}')
        check(rec['comp'] is None or rec['rei'] != round(rec['speed'] * rec['comp'] / 100) or rec['comp'] == 40, f'{loc} rei still uses comp')
        stored = pg.evaluate("JSON.parse(localStorage.getItem('sr-proto-meas-v1'))")
        check(stored[0] == OLD, f'{loc} old record changed {stored[0]}')
        pg.click('#mrBack'); pg.wait_for_timeout(150); pg.evaluate(NAV, 'Progress'); pg.wait_for_timeout(200)
        tab = pg.inner_text('#pgSpeedChart')
        if loc == 'ko-KR':   # 진행 기록은 화면 언어의 기록만 보여 준다 (이전 기록은 한국어)
            check('603*' in tab and '이전 기록은' in tab, f'{loc} old rei not marked: {tab[-300:]}')
        else:
            check('*' not in tab, f'{loc} new-only table should have no old mark')
        check(f"{rec['rei']:,}".rstrip('0').rstrip('.') in tab.replace(',', ',') or str(rec['rei']) in tab.replace(',', ''), f'{loc} new rei not shown in table')
        check(('문항 정답률' if loc == 'ko-KR' else 'Question score') in tab and ('이해도 (9점)' if loc == 'ko-KR' else 'Comprehension (9-pt)') in tab, f'{loc} labels')
        check(not pe, f'{loc} page errors {pe}'); ctx.close()
    b.close()
print('ERR', errs)
