# 오프라인 글꼴 점검 (자체 서버, localhost, 빈 포트).
#  A. 처음 설치: 온라인으로 한 번만 연 뒤(다시 열지 않음) 오프라인 + 브라우저 HTTP 캐시 비움 → 앱 실행.
#  B. 기존 사용자 업데이트: 옛 버전(Google Fonts + sr-v1 서비스 워커) 사용 중 → 새 버전 배포 → 앱을 다시 연 뒤
#     오프라인 + HTTP 캐시 비움 → 앱 실행.
# 두 경우 모두 "앱이 보여 줄 수 있는 모든 글자"(index.html 안의 글자)를 앱이 쓰는 글꼴·굵기마다 불러 보게 해서
# 아직 열지 않은 화면의 글자까지 확인한다. 불러오지 못한 글꼴 조각(status 'error')이 하나도 없어야 한다.
# 여러 화면(한/영, 밝게/어둡게)도 실제로 열어 본다. 외부(Google) 요청은 막는다.
# WebKit은 오프라인 + 서비스 워커 흉내가 안 되므로(pwatest.py 참고) SKIP으로 표시한다. SKIP은 통과가 아니다.
import os, re, json, time, shutil, tempfile, threading, functools, pathlib
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENGINE = os.environ.get('BROWSER', 'chromium')
NEWV = re.search(r"VERSION = '([^']+)'", (ROOT / 'sw.js').read_text(encoding='utf-8')).group(1)
errs = []
def check(c, m):
    if not c: errs.append(m)
if ENGINE == 'webkit':
    print('SKIP: WebKit은 오프라인 서비스 워커 흉내가 안 됨 (실기기에서 확인)'); print('ERR', errs); raise SystemExit

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
def serve(folder):
    srv = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(folder)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f'http://localhost:{srv.server_address[1]}/'
def put_new(d):
    for f in ['index.html', 'privacy.html', 'manifest.webmanifest', 'sw.js']: shutil.copy(ROOT / f, d / f)
    shutil.copytree(ROOT / 'icons', d / 'icons', dirs_exist_ok=True)
    shutil.copytree(ROOT / 'fonts', d / 'fonts', dirs_exist_ok=True)
OLD_SW = re.search(r'OLD_SW = r"""(.*?)"""', (ROOT / 'tests/swtest.py').read_text(encoding='utf-8'), re.S).group(1)   # sr-v1
GOOGLE = ('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
          '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600&family=Barlow+Condensed:wght@500;600&display=swap" rel="stylesheet">')
def put_old(d):
    # 지금 공개 사이트의 옛 버전처럼: Google Fonts를 쓰는 index.html + sr-v1 서비스 워커
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    assert '<link href="fonts/fonts.css" rel="stylesheet">' in html
    (d / 'index.html').write_text(html.replace('<link href="fonts/fonts.css" rel="stylesheet">', GOOGLE), encoding='utf-8')
    for f in ['privacy.html', 'manifest.webmanifest']: shutil.copy(ROOT / f, d / f)
    (d / 'sw.js').write_text(OLD_SW, encoding='utf-8')
    shutil.copytree(ROOT / 'icons', d / 'icons', dirs_exist_ok=True)
    # 이 테스트 서버는 수정 시각(초 단위)으로 "바뀌지 않음(304)"을 판단한다. 새 파일을 같은 초에 덮어쓰면
    # 브라우저가 새 sw.js를 받지 못하므로 옛 파일의 수정 시각을 5초 전으로 돌린다 (길게 돌리면 브라우저가 옛 파일을 캐시에서 꺼냄. GitHub Pages는 내용으로 판단)
    past = time.time() - 5
    for f in d.rglob('*'): os.utime(f, (past, past))
def wait_eval(pg, expr, ms=15000):
    for _ in range(ms // 200):
        if pg.evaluate(expr): return True
        pg.wait_for_timeout(200)
    return False

# 앱이 보여 줄 수 있는 모든 글자로, CSS가 쓰는 글꼴·굵기마다 불러 본다. 불러오지 못한 조각을 돌려준다.
LOAD_ALL = """async () => {
  const text = [...new Set(document.documentElement.outerHTML)].join('');
  const combos = new Set([...document.fonts].map(f => f.weight + ' 16px "' + f.family.replace(/"/g, '') + '"'));
  for (const c of combos){ try { await document.fonts.load(c, text); } catch(e){} }
  const all = [...document.fonts];
  return { faces: all.length, combos: [...combos], loaded: all.filter(f => f.status === 'loaded').length,
           failed: all.filter(f => f.status === 'error').map(f => f.family + ' ' + f.weight + ' ' + f.unicodeRange.slice(0, 24)) };
}"""
SCREENS = ['Training', 'Test', 'Progress', 'Curriculum', 'Dashboard']
NAV = "l => { const b = [...document.querySelectorAll('#tabbar button, .nav button')].find(b => b.offsetParent && b.textContent == l); if (b) b.click(); return !!b; }"

def visit_screens(pg, tag):
    """여러 화면을 실제로 열어 그 화면의 글꼴이 오류 없이 그려지는지."""
    bad = []
    for theme in ['light', 'dark']:
        pg.evaluate("t => document.documentElement.dataset.theme = t", theme)
        for s in SCREENS:
            pg.evaluate(NAV, s); pg.wait_for_timeout(120)
            if s == 'Curriculum': pg.evaluate("document.querySelectorAll('#cuLevels details').forEach(d => d.open = true)")
        pg.evaluate("() => document.fonts.ready")
        bad += pg.evaluate("[...document.fonts].filter(f => f.status === 'error').map(f => f.family + ' ' + f.weight)")
    check(not bad, f'{tag}: 화면을 여는 중 불러오지 못한 글꼴 {sorted(set(bad))[:6]}')

def offline_check(ctx, base, tag):
    pg = ctx.new_page(); pe = []; pg.on('pageerror', lambda e: pe.append(str(e)))
    cdp = ctx.new_cdp_session(pg); cdp.send('Network.clearBrowserCache')   # 서비스 워커 캐시만 남긴다
    ctx.set_offline(True)
    try: pg.goto(base, wait_until='load', timeout=15000)
    except Exception as e: check(False, f'{tag}: 오프라인 실행 실패 {str(e)[:80]}'); return
    pg.wait_for_timeout(400)
    check(pg.evaluate("!!document.querySelector('#dash')"), f'{tag}: 오프라인에서 앱이 열리지 않음')
    ext = pg.evaluate("[...document.styleSheets].map(s => s.href || '').filter(h => h && !h.startsWith(location.origin))")
    check(not ext, f'{tag}: 외부 스타일시트 {ext}')
    for lang in ['ko', 'en']:
        if lang == 'en': pg.evaluate("() => { const b = [...document.querySelectorAll('button')].find(b => b.offsetParent && b.textContent.trim() == 'EN'); if (b) b.click(); }"); pg.wait_for_timeout(200)
        visit_screens(pg, f'{tag} {lang}')
    r = pg.evaluate(LOAD_ALL)
    print(f'{tag}: faces {r["faces"]}, loaded {r["loaded"]}, failed {len(r["failed"])}', r['combos'])
    check(r['faces'] > 0, f'{tag}: 글꼴 정의가 없음 (fonts.css를 불러오지 못함)')
    check(not r['failed'], f'{tag}: 오프라인에서 불러오지 못한 글꼴 조각 {len(r["failed"])}개, 예: {r["failed"][:4]}')
    check(not pe, f'{tag}: 페이지 오류 {pe[:2]}')
    ctx.set_offline(False); pg.close()

with sync_playwright() as p:
    b = p.chromium.launch()

    # A. 처음 설치
    d = pathlib.Path(tempfile.mkdtemp(prefix='fonttest-')); put_new(d); srv, base = serve(d)
    ctx = b.new_context(viewport={'width': 1280, 'height': 900}, locale='ko-KR')
    ctx.route(re.compile(r'^https?://(?!localhost)'), lambda r: r.abort())
    pg = ctx.new_page(); pg.goto(base, wait_until='load')
    check(wait_eval(pg, "navigator.serviceWorker.ready.then(r => !!r.active && r.active.state === 'activated')"), 'A: 서비스 워커가 활성화되지 않음')
    pg.wait_for_timeout(300)
    keys = pg.evaluate("caches.open('%s').then(c => c.keys()).then(ks => ks.map(k => new URL(k.url).pathname))" % NEWV)
    n_font = sum(1 for k in keys if k.endswith('.woff2'))
    print('A install cache:', len(keys), 'entries,', n_font, 'woff2')
    pg.close()
    offline_check(ctx, base, 'A 처음 설치')
    ctx.close(); srv.shutdown(); shutil.rmtree(d, ignore_errors=True)

    # B. 옛 버전에서 업데이트
    d = pathlib.Path(tempfile.mkdtemp(prefix='fonttest-')); put_old(d); srv, base = serve(d)
    ctx = b.new_context(viewport={'width': 1280, 'height': 900}, locale='ko-KR')
    ctx.route(re.compile(r'^https?://(?!localhost)'), lambda r: r.abort())
    pg = ctx.new_page(); pg.goto(base, wait_until='load')
    pg.evaluate("navigator.serviceWorker.ready.then(() => true)"); pg.reload(); pg.wait_for_timeout(300)
    old_v = pg.evaluate("caches.keys()")
    put_new(d)                                    # 새 버전 배포
    pg.reload(); pg.wait_for_timeout(300)         # 앱을 다시 연다 → 새 서비스 워커 설치·활성화
    check(wait_eval(pg, "caches.keys().then(ks => ks.length === 1 && ks[0] === '%s')" % NEWV), 'B: 새 캐시로 바뀌지 않음')
    pg.reload(); pg.wait_for_timeout(300)
    print('B caches before/after:', old_v, pg.evaluate("caches.keys()"))
    pg.close()
    offline_check(ctx, base, 'B 업데이트')
    ctx.close(); srv.shutdown(); shutil.rmtree(d, ignore_errors=True)
    b.close()
print('ERR', errs)
