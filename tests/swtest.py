# 오프라인 캐시(서비스 워커) 점검. 이 테스트는 자기 서버를 직접 띄운다 (임시 폴더, localhost, 빈 포트).
#  A. 새 서비스 워커: 온라인 실행 → 오프라인 재실행 → 개인정보처리방침 방문 후 오프라인 앱 실행
#     → 오프라인 개인정보처리방침 → 재연결 후 실행. 캐시 항목이 페이지마다 따로 저장되는지.
#  B. 기존 사용자(sr-v1): 옛 서비스 워커에서 오류가 재현되는지 → 새 sw.js로 바뀌면 옛 캐시가 지워지고
#     오프라인 앱이 정상인지, 학습 기록·설정(localStorage)이 그대로인지.
# Playwright WebKit은 오프라인 흉내 + 서비스 워커 조합에서 내부 오류를 내므로(pwatest.py 참고)
# WebKit에서는 오프라인 단계를 건너뛰고 "SKIP"으로 표시한다. 건너뛴 단계는 통과가 아니다.
import os, json, shutil, tempfile, threading, functools, pathlib
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENGINE = os.environ.get('BROWSER', 'chromium')
OFFLINE_OK = ENGINE != 'webkit'
NEW_SW = (ROOT / 'sw.js').read_text(encoding='utf-8')
# 2026-11-18 이전 sw.js (sr-v1). 탐색한 모든 페이지를 './index.html' 하나에 덮어써서 오류가 났다.
OLD_SW = r"""/* Offline support: app shell cached on install, fonts cached on first use. */
const VERSION = 'sr-v1';
const SHELL = ['./', './index.html', './manifest.webmanifest', './privacy.html',
  './icons/icon-192.png', './icons/icon-512.png', './icons/maskable-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (req.mode === 'navigate'){
    e.respondWith(fetch(req).then(r => { const copy = r.clone(); caches.open(VERSION).then(c => c.put('./index.html', copy)); return r; })
      .catch(() => caches.match('./index.html')));
    return;
  }
  if (url.origin === location.origin || /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)){
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => {
      if (r.ok || r.type === 'opaque'){ const copy = r.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
      return r;
    })));
  }
});
"""
KEYS = ['sr-proto-v1', 'sr-proto-meas-v1', 'sr-proto-calib-v1', 'sr-proto-prefs-v1', 'sr-proto-cfg-v1', 'sr-proto-prog-v1']
SEED = {
  'sr-proto-v1': [{'frame': 'A-I', 'preset': 'day1', 'aborted': False, 'trainSec': 180, 'date': '2026-10-20', 'ts': 1}],
  'sr-proto-meas-v1': [{'lang': 'ko', 'date': '2026-10-20', 'count': 812, 'ts': 2}],
  'sr-proto-calib-v1': {'pxPerMm': 3.9, 'distance': 40},
  'sr-proto-prog-v1': {'day': 3, 'done': {}},
}
errs, skips = [], []
def check(c, m):
    if not c: errs.append(m)

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
def serve(folder):
    srv = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(folder)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f'http://localhost:{srv.server_address[1]}/'
def site(sw_text):
    d = pathlib.Path(tempfile.mkdtemp(prefix='swtest-'))
    for f in ['index.html', 'privacy.html', 'manifest.webmanifest']: shutil.copy(ROOT / f, d / f)
    shutil.copytree(ROOT / 'icons', d / 'icons')
    (d / 'sw.js').write_text(sw_text, encoding='utf-8')
    return d

def what(pg):  # 지금 보이는 페이지가 앱인지, 개인정보처리방침인지
    return pg.evaluate("document.querySelector('#dash') ? 'app' : (/개인정보처리방침|Privacy/.test(document.title) ? 'privacy' : 'other:' + document.title)")
def open_page(pg, url):
    try: pg.goto(url, wait_until='load', timeout=15000); pg.wait_for_timeout(300); return what(pg)
    except Exception as e: return 'error:' + str(e).splitlines()[0][:80]
def controlled(pg, base):
    # 서비스 워커가 설치·활성화되고 이 페이지를 제어할 때까지
    pg.evaluate("navigator.serviceWorker.ready.then(() => true)")
    if not pg.evaluate("!!navigator.serviceWorker.controller"): pg.reload(); pg.wait_for_timeout(300)
    return pg.evaluate("!!navigator.serviceWorker.controller")
CACHE_STATE = """async () => {
  const keys = await caches.keys(), out = { keys };
  for (const k of keys){ const c = await caches.open(k);
    for (const [name, path] of [['app', './index.html'], ['privacy', './privacy.html']]){
      const r = await c.match(path); const t = r ? await r.text() : '';
      out[k + ':' + name] = !r ? 'none' : (t.includes('id="dash"') ? 'app' : (t.includes('개인정보처리방침') ? 'privacy' : 'other')); } }
  return out; }"""
def offline_step(label, fn):
    if OFFLINE_OK: fn()
    else: skips.append(label); print('SKIP (WebKit 도구 한계):', label)

with sync_playwright() as p:
    b = getattr(p, ENGINE).launch()

    # ---------- A. 새 서비스 워커 ----------
    d = site(NEW_SW); srv, base = serve(d)
    ctx = b.new_context(locale='ko-KR'); pg = ctx.new_page(); pe = []; pg.on('pageerror', lambda e: pe.append(str(e)))
    r = open_page(pg, base + '?source=app'); print('A1 online launch:', r); check(r == 'app', f'A1 online launch {r}')
    check(controlled(pg, base), 'A1 service worker not controlling the page')
    st = pg.evaluate(CACHE_STATE); print('   cache:', st)
    check(st['keys'] == ['sr-v2'], f'A1 cache keys {st["keys"]}')
    check(st.get('sr-v2:app') == 'app' and st.get('sr-v2:privacy') == 'privacy', f'A1 shell entries {st}')
    def a2():
        ctx.set_offline(True)
        r = open_page(pg, base + '?source=app'); print('A2 offline relaunch:', r); check(r == 'app', f'A2 offline relaunch {r}')
        ctx.set_offline(False)
    offline_step('A2 앱 실행 후 오프라인 재실행', a2)
    r = open_page(pg, base + 'privacy.html'); print('A3 online privacy:', r); check(r == 'privacy', f'A3 online privacy {r}')
    st = pg.evaluate(CACHE_STATE); print('   cache after privacy visit:', st)
    check(st.get('sr-v2:app') == 'app', f'A3 app entry overwritten {st}')   # 오류의 직접 원인: 앱 항목이 덮이면 안 된다
    def a4():
        ctx.set_offline(True)
        for u in ['?source=app', '', 'index.html']:
            r = open_page(pg, base + u); print(f'A4 offline app after privacy visit ({u or "/"}):', r); check(r == 'app', f'A4 offline app {u} {r}')
        r = open_page(pg, base + 'privacy.html'); print('A5 offline privacy:', r); check(r == 'privacy', f'A5 offline privacy {r}')
        ctx.set_offline(False)
    offline_step('A4 개인정보처리방침 방문 후 오프라인 앱 실행 / A5 오프라인 개인정보처리방침', a4)
    # 재연결 후: 서버에 새 내용이 있으면 그것을 받아야 한다 (network first)
    # 앱 스크립트가 제목을 바꾸므로, 표시용 주석으로 새 내용이 왔는지 본다
    (d / 'index.html').write_text((ROOT / 'index.html').read_text(encoding='utf-8').replace('<head>', '<head><!--swtest-v-next-->', 1), encoding='utf-8')
    r = open_page(pg, base + '?source=app'); fresh = pg.evaluate("document.documentElement.outerHTML.includes('swtest-v-next')")
    print('A6 reconnect:', r, '| fresh from network:', fresh)
    check(r == 'app' and fresh, f'A6 reconnect did not load fresh page {r} {fresh}')
    st = pg.evaluate(CACHE_STATE); check(st.get('sr-v2:app') == 'app', f'A6 app entry after reconnect {st}')
    check(not pe, f'A page errors {pe}')
    ctx.close(); srv.shutdown(); shutil.rmtree(d, ignore_errors=True)

    # ---------- B. 기존 사용자 (sr-v1 → sr-v2) ----------
    d = site(OLD_SW); srv, base = serve(d)
    ctx = b.new_context(locale='ko-KR'); pg = ctx.new_page(); pe = []; pg.on('pageerror', lambda e: pe.append(str(e)))
    open_page(pg, base + '?source=app')
    pg.evaluate("s => { localStorage.clear(); for (const k in s) localStorage.setItem(k, JSON.stringify(s[k])); localStorage.setItem('swtest-sentinel', 'keep'); }", SEED)
    check(controlled(pg, base), 'B1 old service worker not controlling')
    # 앱이 저장값을 스스로 정리(예: 보정 기본값 채우기)한 뒤의 상태를 기준으로 삼는다
    pg.reload(); pg.wait_for_timeout(300)
    before = pg.evaluate("k => Object.fromEntries(k.map(x => [x, localStorage.getItem(x)]))", KEYS)
    open_page(pg, base + 'privacy.html')
    st = pg.evaluate(CACHE_STATE); print('B1 old sw after privacy visit:', st)
    check(st.get('sr-v1:app') == 'privacy', f'B1 bug not reproduced with old sw {st}')   # 옛 버전에서는 앱 항목이 개인정보처리방침으로 덮인다
    def b2():
        ctx.set_offline(True)
        r = open_page(pg, base + '?source=app'); print('B2 old sw offline app (bug expected):', r); check(r == 'privacy', f'B2 bug not reproduced {r}')
        ctx.set_offline(False)
    offline_step('B2 옛 서비스 워커에서 오류 재현 (오프라인)', b2)
    # 새 sw.js 배포 → 온라인으로 앱을 열면 브라우저가 새 버전을 받아 설치한다
    (d / 'sw.js').write_text(NEW_SW, encoding='utf-8')
    open_page(pg, base + '?source=app')
    pg.evaluate("navigator.serviceWorker.getRegistration().then(r => r && r.update())")
    for _ in range(50):
        if pg.evaluate("caches.keys()") == ['sr-v2']: break
        pg.wait_for_timeout(200)
    open_page(pg, base + '?source=app')
    st = pg.evaluate(CACHE_STATE); print('B3 after update:', st)
    check(st['keys'] == ['sr-v2'], f'B3 old cache not removed {st["keys"]}')
    check(st.get('sr-v2:app') == 'app' and st.get('sr-v2:privacy') == 'privacy', f'B3 new entries {st}')
    def b4():
        ctx.set_offline(True)
        r = open_page(pg, base + '?source=app'); print('B4 offline app after update:', r); check(r == 'app', f'B4 offline app after update {r}')
        r = open_page(pg, base + 'privacy.html'); print('B4 offline privacy after update:', r); check(r == 'privacy', f'B4 offline privacy {r}')
        ctx.set_offline(False)
    offline_step('B4 업데이트 뒤 오프라인 앱·개인정보처리방침', b4)
    open_page(pg, base + '?source=app')
    after = pg.evaluate("k => Object.fromEntries(k.map(x => [x, localStorage.getItem(x)]))", KEYS)
    for k, v in SEED.items():  # 넣어 둔 기록이 그대로 남아 있다 (앱이 덧붙인 기본값은 허용)
        a = json.loads(after[k]); check(a == v if isinstance(v, list) else all(a.get(f) == x for f, x in v.items()), f'B5 {k} changed')
    check(all(after[k] == before[k] for k in KEYS), f'B5 stored values changed {before} {after}')
    check(pg.evaluate("localStorage.getItem('swtest-sentinel')") == 'keep', 'B5 sentinel lost')
    print('B5 records kept:', all(after[k] == before[k] for k in KEYS))
    check(not pe, f'B page errors {pe}')
    ctx.close(); srv.shutdown(); shutil.rmtree(d, ignore_errors=True)
    b.close()
print('SKIPPED', skips)
print('ERR', errs)
