# 기록 백업: 내보내기 → 저장공간 비우기 → 가져오기로 똑같이 되살아나는지, 잘못된 파일·취소는 기록을 건드리지 않는지
import os, json, pathlib
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = 'http://localhost:8765/'   # file:// 은 브라우저마다 저장공간이 달라 http로 연다
TMP = pathlib.Path(__file__).resolve().parent / '_backup_tmp'
TMP.mkdir(exist_ok=True)
KEYS = ['sr-proto-v1', 'sr-proto-meas-v1', 'sr-proto-calib-v1', 'sr-proto-prefs-v1', 'sr-proto-cfg-v1', 'sr-proto-prog-v1']
SEED = {
  'sr-proto-v1': [{'frame': 'A-I', 'preset': 'day1', 'aborted': False, 'trainSec': 180, 'date': '2026-10-20', 'ts': 1}],
  'sr-proto-meas-v1': [{'lang': 'ko', 'date': '2026-10-20', 'count': 812, 'ts': 2}],
  'sr-proto-calib-v1': {'pxPerMm': 3.9, 'distance': 40},
  'sr-proto-prog-v1': {'day': 3, 'done': {}},
}
errs = []
def check(c, m):
    if not c: errs.append(m)
def snap(pg): return pg.evaluate("k => Object.fromEntries(k.map(x => [x, localStorage.getItem(x)]))", KEYS)
def to_prog(pg):
    pg.evaluate("[...document.querySelectorAll('#tabbar button, .nav button')].find(b => b.offsetParent && b.textContent == 'Progress').click()"); pg.wait_for_timeout(100)
with sync_playwright() as p:
    b = getattr(p, os.environ.get('BROWSER', 'chromium')).launch()
    for loc, vp in [('ko-KR', (390, 844)), ('en-US', (1366, 900))]:
        ctx = b.new_context(viewport={'width': vp[0], 'height': vp[1]}, locale=loc, accept_downloads=True)
        pg = ctx.new_page(); pe = []; pg.on('pageerror', lambda e: pe.append(str(e)))
        pg.goto(URL); pg.evaluate("s => { localStorage.clear(); for (const k in s) localStorage.setItem(k, JSON.stringify(s[k])); }", SEED)
        pg.reload(); pg.wait_for_timeout(200); to_prog(pg)
        before = snap(pg)
        check(pg.is_visible('#bkExport') and pg.is_visible('#bkImport'), 'backup buttons not visible')
        with pg.expect_download() as dl: pg.click('#bkExport')
        d = dl.value; f = TMP / d.suggested_filename; d.save_as(f)
        data = json.loads(f.read_text())
        print(loc, 'file', d.suggested_filename, 'keys', sorted(data['data']), 'msg', pg.inner_text('#bkMsg'))
        check(d.suggested_filename.startswith('speedread-backup-') and data['app'] == 'speedread' and data['v'] == 1, 'bad export header')
        check(data['data']['sr-proto-prog-v1']['day'] == 3, 'export missing prog')
        # 저장공간을 비우고 가져오기
        pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(200); to_prog(pg)
        msgs = []
        pg.once('dialog', lambda dg: (msgs.append(dg.message), dg.accept()))
        with pg.expect_navigation(): pg.set_input_files('#bkFile', str(f))
        pg.wait_for_timeout(200)
        after = snap(pg)
        print('  confirm:', msgs[0][:80] if msgs else None)
        check(msgs and '3' in msgs[0], 'confirm text missing day')
        for k in KEYS:
            if before[k] is None: check(after[k] is None, f'{k} should stay empty')
            else: check(json.loads(after[k]) == json.loads(before[k]), f'{k} not restored')
        # 취소하면 바뀌지 않는다
        other = dict(data); other['data'] = dict(data['data']); other['data']['sr-proto-prog-v1'] = {'day': 9, 'done': {}}
        g = TMP / 'other.json'; g.write_text(json.dumps(other))
        to_prog(pg); pg.once('dialog', lambda dg: dg.dismiss()); pg.set_input_files('#bkFile', str(g)); pg.wait_for_timeout(200)
        check(json.loads(snap(pg)['sr-proto-prog-v1'])['day'] == 3, 'cancel changed records')
        print('  cancel msg:', pg.inner_text('#bkMsg'))
        # 잘못된 파일은 거부
        for bad in ['not json', json.dumps({'app': 'other', 'v': 1, 'data': {}}), json.dumps({'app': 'speedread', 'v': 1, 'data': {'evil': 1}}),
                    json.dumps({'app': 'speedread', 'v': 1, 'data': {'sr-proto-v1': 'x'}})]:
            h = TMP / 'bad.json'; h.write_text(bad)
            pg.set_input_files('#bkFile', str(h)); pg.wait_for_timeout(150)
            check(json.loads(snap(pg)['sr-proto-prog-v1'])['day'] == 3, 'bad file changed records')
        print('  bad msg:', pg.inner_text('#bkMsg'))
        check(not pe, f'page errors {pe}'); ctx.close()
for x in TMP.iterdir(): x.unlink()
TMP.rmdir()
print('ERR', errs)
