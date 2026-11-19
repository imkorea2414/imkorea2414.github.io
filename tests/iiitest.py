# 사방훈련(C-III·D-III) 4곳 + 1 최종 점검 (2026-11-19)
#  1. 가장 어려운 곳 고르기: 도입 정확도가 가장 낮은 곳, 같으면 앞 번호, 정확도가 없는 곳은 빼고, 모두 없으면 추가 훈련 없음
#  2. 실제 진행: III-2만 원을 짚지 않으면 III-1 → 2 → 3 → 4 → 2 순서, 기록·훈련 시간(5 × 1분)·오늘 완료 표시
#  3. 중도 종료: 3번째 곳에서 그만두면 "중단" 기록, 해낸 곳의 정확도만 남고 오늘 완료로 치지 않음
#  4. 결과 화면 "그곳만 다시": 그 훈련(D-III면 D-III)의 그 한 곳만 (4곳 + 1을 다시 하지 않음)
#  5. 예상 시간: 계획 시간 4곳 + 1, 다른 시간에서 "4곳 모두"를 골라도 4곳 + 1로 셈
#  6. 백업: 이전 형식 기록(한 곳만 한 사방훈련, 설정 part '2')과 새 기록을 가져와도 오류 없이 표시, 계획은 4곳 + 1
import os, json, re, tempfile, pathlib
from playwright.sync_api import sync_playwright
# 앱 코드는 함수 안에 있으므로, 테스트용 사본에서만 내부 값을 window.__t로 꺼내 본다 (앱 파일은 그대로)
SRC = pathlib.Path(__file__).resolve().parent.parent.joinpath('index.html').read_text(encoding='utf-8')
HOOK = ("window.__t = { get S(){ return S; }, set S(v){ S = v; }, get G(){ return G; }, get PLAN(){ return PLAN; }, "
        "weakestPart, estMin, presetOf, presetSel, cfg, planSel, dayPlan, doneToday, DRILLS };\n})();\n</script>")
assert SRC.count("})();\n</script>") == 1
TMP = pathlib.Path(tempfile.mkdtemp(prefix='iiitest-')) / 'index.html'
TMP.write_text(SRC.replace("})();\n</script>", HOOK), encoding='utf-8')
URL = TMP.as_uri()
ENGINE = os.environ.get('BROWSER', 'chromium')
CAL = {'pxPerMm': 3.9, 'distance': 40}
errs = []
def check(c, m):
    if not c: errs.append(m)

def ctx_page(b, day, extra=None, loc='ko-KR'):
    ctx = b.new_context(viewport={'width': 1280, 'height': 900}, locale=loc)
    pg = ctx.new_page(); pe = []; pg.on('pageerror', lambda e: pe.append(str(e)))
    seed = {'sr-proto-calib-v1': CAL, 'sr-proto-prog-v1': {'day': day, 'done': {}}}
    seed.update(extra or {})
    pg.add_init_script("(s => { if (!sessionStorage.getItem('seeded')) { localStorage.clear(); for (const k in s) localStorage.setItem(k, JSON.stringify(s[k])); sessionStorage.setItem('seeded', '1'); } })(" + json.dumps(seed) + ")")
    pg.clock.install(); pg.goto(URL); pg.wait_for_timeout(250)
    return ctx, pg, pe

def open_row(pg, text):
    pg.locator('#todayRows li button', has_text=text).first.click(); pg.wait_for_timeout(200)
    if pg.evaluate("document.querySelector('#calib').classList.contains('on')"): pg.click('#calibSave'); pg.wait_for_timeout(200)

# 도입 때 III-{skip}에서만 원을 짚지 않는다 (나머지 곳은 원 위를 짚는다)
AIM = """skip => setInterval(() => { if (!__t.S || __t.S.phase !== 'intro' || !__t.G) return;
  if (__t.S.parts[__t.S.partI] === skip) { __t.S.ptr = null; return; }
  const t = __t.G.pts[__t.G.seq[__t.S.pos]]; __t.S.ptr = { x: t.x, y: t.y }; }, 50)"""

def run(pg, until_check=True, quit_at=None, limit=200):
    """5초씩 진행하며 지나간 곳을 기록. quit_at = (곳 순번, 'train')이면 그 곳 훈련 중에 그만둔다."""
    seen = []
    for _ in range(limit):
        pg.clock.run_for(5000); pg.wait_for_timeout(5)
        if pg.evaluate("document.querySelector('#check').classList.contains('on')"): break
        st = pg.evaluate("__t.S ? [__t.S.parts ? __t.S.parts.slice() : null, __t.S.partI, __t.S.phase] : null")
        if st and st[0] and (not seen or seen[-1] != (st[1], st[0][st[1]])): seen.append((st[1], st[0][st[1]]))
        if quit_at and st and st[1] == quit_at[0] and st[2] == quit_at[1]:
            pg.click('#pauseBtn'); pg.click('#quitBtn'); pg.wait_for_timeout(100); break
    return [p for _, p in seen]

with sync_playwright() as p:
    b = getattr(p, ENGINE).launch()

    # 1. 고르는 규칙 (원전 p.73 ④·p.111 ⑤ "가장 안 되는 곳", 정확도로 판단하는 것은 설계)
    ctx, pg, pe = ctx_page(b, 8)
    cases = [([80, 40, 90, 70], 2), ([50, 30, 30, 90], 2), ([0, 0, 0, 0], 1), ([None, 60, None, 40], 4),
             ([None, None, None, None], None), ([90, 90, 90, 95, 10], 1)]
    for accs, want in cases:
        got = pg.evaluate("a => { __t.S = { partStat: a.map((x, i) => ({ part: i < 4 ? i + 1 : 1, acc: x })) }; const w = __t.weakestPart(); __t.S = null; return w; }", accs)
        check(got == want, f'weakestPart {accs} -> {got}, expected {want}')
    check(not pe, f'rule page errors {pe}'); ctx.close()

    # 2. Day 8 C-III 끝까지: III-2만 짚지 않음
    ctx, pg, pe = ctx_page(b, 8)
    est_plan = pg.evaluate("__t.estMin()")
    exp_plan = pg.evaluate("(() => { let s = 180; __t.PLAN.items.forEach(i => { if (i.soon || i.id === 'measure') return; const p = __t.presetOf(i.id); s += (p.intro + p.train * __t.cfg[i.id].rounds) * (i.part === 'all4' ? 5 : 1) + (i.review ? i.review[0] : 0); }); return Math.ceil(s / 60); })()")
    check(est_plan == exp_plan, f'estimate {est_plan} != {exp_plan}')
    pg.evaluate(AIM, 2)
    open_row(pg, 'C-III'); pg.click('#briefGo')
    seen = run(pg)
    print('C-III order:', seen)
    check(seen == [1, 2, 3, 4, 2], f'C-III order {seen}')
    pg.click('#toResult'); pg.wait_for_timeout(200)
    rec = pg.evaluate("JSON.parse(localStorage.getItem('sr-proto-v1')).slice(-1)[0]")
    print('record:', {k: rec.get(k) for k in ['frame', 'parts', 'partStat', 'trainSec', 'aborted', 'rounds']})
    accs = {s['part']: s['acc'] for s in rec['partStat'][:4]}
    check(rec['parts'] == [1, 2, 3, 4, 2] and not rec['aborted'], f'record parts {rec["parts"]}')
    check(accs[2] < 30 and min(accs[1], accs[3], accs[4]) > 70, f'accuracies {accs}')
    check(abs(rec['trainSec'] - 300) <= 3, f'train time {rec["trainSec"]} (5 × 60)')
    check('III-2' in pg.inner_text('#rPart'), 'result does not name III-2 as hardest')
    check(pg.evaluate("__t.doneToday()['C-III']") is True, 'C-III not marked done today')
    # 4. 그곳만 다시 → C-III, III-2 한 곳
    pg.click('#partRetry'); pg.wait_for_timeout(200)
    st = pg.evaluate("[__t.S.D.id, __t.S.parts.slice()]")
    check(st == ['C-III', [2]], f'retry C-III {st}')
    check(not pe, f'C-III page errors {pe}'); ctx.close()

    # 3. 중도 종료: 3번째 곳 훈련 중
    ctx, pg, pe = ctx_page(b, 8)
    pg.evaluate(AIM, 0)
    open_row(pg, 'C-III'); pg.click('#briefGo')
    seen = run(pg, quit_at=(2, 'train'))
    pg.wait_for_timeout(100)
    check(pg.evaluate("document.querySelector('#check').classList.contains('on')"), 'quit did not reach check screen')
    pg.click('#toResult'); pg.wait_for_timeout(200)
    rec = pg.evaluate("JSON.parse(localStorage.getItem('sr-proto-v1')).slice(-1)[0]")
    print('quit record:', {k: rec.get(k) for k in ['parts', 'partStat', 'trainSec', 'aborted']})
    check(rec['aborted'] is True, 'quit record not aborted')
    check([s['part'] for s in rec['partStat'] if s] == [1, 2, 3], f'quit partStat {rec["partStat"]}')
    check(pg.evaluate("__t.doneToday()['C-III']") is False, 'aborted C-III counted as done')
    check('TRAINING STOPPED' in pg.inner_text('#rHead'), 'result head not STOPPED')
    check(not pe, f'quit page errors {pe}'); ctx.close()

    # D-III가 나오는 날 찾기 → 끝까지 → 그곳만 다시는 D-III
    ctx, pg, pe = ctx_page(b, 1)
    dday = pg.evaluate("[...Array(48)].map((_, i) => i + 1).find(d => __t.dayPlan(d).items.some(i => i.id === 'D-III'))")
    ctx.close()
    ctx, pg, pe = ctx_page(b, dday)
    pg.evaluate(AIM, 3)
    open_row(pg, 'D-III'); pg.click('#briefGo')
    seen = run(pg)
    print(f'D-III (Day {dday}) order:', seen)
    check(seen == [1, 2, 3, 4, 3], f'D-III order {seen}')
    pg.click('#toResult'); pg.wait_for_timeout(200)
    pg.click('#partRetry'); pg.wait_for_timeout(200)
    st = pg.evaluate("[__t.S.D.id, __t.S.parts.slice()]")
    check(st == ['D-III', [3]], f'retry D-III {st} (was C-III before the fix)')
    check(not pe, f'D-III page errors {pe}'); ctx.close()

    # 5. 계획이 아닌 시간 + 4곳 모두 → 예상 시간도 4곳 + 1
    ctx, pg, pe = ctx_page(b, 8)
    r = pg.evaluate("""(() => { const a = __t.estMin(); __t.planSel['C-III'] = __t.DRILLS['C-III'].presets[0].k; __t.cfg['C-III'].part = 'all';
      const p = __t.presetOf('C-III'), b = __t.estMin(); return [a, b, p.intro, p.train, __t.cfg['C-III'].rounds, __t.presetSel('C-III')]; })()""")
    a, bb, intro, train, rounds, sel = r
    print('estimate plan / other preset all:', r)
    check(sel != 'plan', 'could not select a non-plan preset')
    check(pg.evaluate("(() => { let s = 180; __t.PLAN.items.forEach(i => { if (i.soon || i.id === 'measure') return; const p = __t.presetOf(i.id), n = i.id === 'C-III' ? 5 : (i.part === 'all4' ? 5 : 1); s += (p.intro + p.train * __t.cfg[i.id].rounds) * n + (i.review ? i.review[0] : 0); }); return Math.ceil(s / 60); })()") == bb,
          f'non-plan all estimate {bb} not 4 + 1')
    ctx.close()

    # 6. 백업 호환: 이전 형식 + 새 형식 기록 가져오기
    old_rec = {'date': '2026-11-01', 'ts': 1, 'frame': 'C-III', 'trainSec': 60, 'rounds': 1, 'roundsTotal': 1, 'passes': 30, 'pace': 1,
               'accuracy': 70, 'aborted': False, 'reactions': [], 'preset': 'plan', 'turns': 0, 'turnAvgMs': None,
               'parts': [2], 'partStat': [{'part': 2, 'acc': 70}]}
    old_all = dict(old_rec, ts=2, parts=[1, 2, 3, 4], partStat=[{'part': i, 'acc': 60 + i} for i in range(1, 5)], trainSec=240)
    new_rec = dict(old_rec, ts=3, parts=[1, 2, 3, 4, 2], partStat=[{'part': 1, 'acc': 90}, {'part': 2, 'acc': 20}, {'part': 3, 'acc': 90}, {'part': 4, 'acc': 90}], trainSec=300)
    bk = {'app': 'speedread', 'v': 1, 'exportedAt': '2026-11-19T00:00:00Z',
          'data': {'sr-proto-v1': [old_rec, old_all, new_rec], 'sr-proto-prog-v1': {'day': 8, 'done': {}}, 'sr-proto-calib-v1': CAL,
                   'sr-proto-cfg-v1': {'C-III': {'preset': 'plan', 'rounds': 1, 'part': '2'}}}}
    f = pathlib.Path(tempfile.mkdtemp()) / 'bk.json'; f.write_text(json.dumps(bk))
    ctx, pg, pe = ctx_page(b, 1)
    pg.evaluate("document.querySelectorAll('#tabbar button, .nav button').forEach(b => { if (b.offsetParent && b.textContent == 'Progress') b.click(); })")
    pg.on('dialog', lambda d: d.accept())
    pg.set_input_files('#bkFile', str(f)); pg.wait_for_timeout(600)
    n = pg.evaluate("JSON.parse(localStorage.getItem('sr-proto-v1') || '[]').length")
    check(n == 3, f'imported records {n}')
    for s in ['Progress', 'Training', 'Dashboard']:
        pg.evaluate("l => [...document.querySelectorAll('#tabbar button, .nav button')].find(b => b.offsetParent && b.textContent == l).click()", s); pg.wait_for_timeout(150)
    rows = pg.inner_text('#todayRows')
    check('C-III' in rows and '4곳 + 가장 어려웠던 곳 1회' in rows, f'after import, plan is not 4 + 1: {rows[:200]}')
    open_row(pg, 'C-III')
    check('× 4곳 + 1' in pg.inner_text('#sumRounds'), 'after import, brief is not 4 + 1')
    check(not pe, f'backup page errors {pe}'); ctx.close()
    b.close()
print('ERR', errs)
