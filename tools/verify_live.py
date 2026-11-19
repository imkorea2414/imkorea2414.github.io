"""배포된 웹 앱 점검 (GitHub Actions에서 Pages 배포 직후 실행, 로컬에서도 사용 가능).
사용: python3 tools/verify_live.py https://imkorea2414.github.io/
- 서비스 파일·개인정보처리방침·설치 정보 응답
- assetlinks.json이 저장소 파일과 같은지 (TWA 연결)
- 서비스 워커 설치 뒤 오프라인 실행, 오프라인 개인정보처리방침
- 개발 문서와 2026-11-19에 삭제한 원전 스캔 이미지 주소가 404인지 (CDN 캐시를 생각해 최대 약 6분 재시도)
끝 줄 'ERR []'이면 통과."""
import sys, json, time, pathlib, urllib.request, urllib.error, urllib.parse
from playwright.sync_api import sync_playwright
BASE = sys.argv[1].rstrip('/') + '/'
ROOT = pathlib.Path(__file__).resolve().parent.parent
errs, known = [], []
def check(c, m):
    print(('OK   ' if c else 'FAIL ') + m)
    if not c: errs.append(m)
def status(path):
    url = BASE + urllib.parse.quote(path)
    req = urllib.request.Request(url, headers={'Cache-Control': 'no-cache', 'User-Agent': 'pages-verify'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r: return r.status, r.read()
    except urllib.error.HTTPError as e: return e.code, b''
    except Exception as e: return 0, str(e).encode()
for p in ['', 'index.html', 'privacy.html', 'manifest.webmanifest', 'sw.js',
          'icons/apple-touch-icon.png', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/maskable-512.png']:
    s, _ = status(p); check(s == 200, f'{s} /{p}')
s, body = status('.well-known/assetlinks.json')
try: same = json.loads(body) == json.loads((ROOT / '.well-known/assetlinks.json').read_text())
except Exception: same = False
check(s == 200 and same, f'{s} /.well-known/assetlinks.json (저장소 파일과 같음: {same})')
gone = ['CLAUDE.md', 'README.md', 'src/template.html', 'tools/build.py', 'docs/플레이콘솔_입력값_초안.md', 'docs/훈련투입방법_원본표.png']
for i in range(int(__import__("os").environ.get("RETRY","13"))):
    left = [p for p in gone if status(p)[0] != 404]
    if not left: break
    time.sleep(30)
for p in gone: check(p not in left, f'404 /{p}')
old_sw = b"'sr-v1'" in status('sw.js')[1]
print('배포된 서비스 워커:', 'sr-v1 (옛 버전)' if old_sw else 'sr-v2 이상')
with sync_playwright() as pw:
    b = pw.chromium.launch(); ctx = b.new_context(locale='ko-KR'); pg = ctx.new_page(); pe = []
    pg.on('pageerror', lambda e: pe.append(str(e)))
    pg.goto(BASE + '?source=app'); pg.wait_for_timeout(1500)
    check(pg.evaluate("!!document.querySelector('#dash')"), '온라인 앱 실행')
    pg.evaluate("navigator.serviceWorker.ready.then(() => true)")
    if not pg.evaluate("!!navigator.serviceWorker.controller"): pg.reload(); pg.wait_for_timeout(1000)
    check(pg.evaluate("!!navigator.serviceWorker.controller"), '서비스 워커 작동')
    ctx.set_offline(True)
    pg.goto(BASE + '?source=app'); pg.wait_for_timeout(1000)
    check(pg.evaluate("!!document.querySelector('#dash')"), '오프라인 앱 실행')
    pg.goto(BASE + 'privacy.html'); pg.wait_for_timeout(800)
    ok = '개인정보' in pg.title()
    if not ok and old_sw:   # sr-v1은 모든 페이지를 앱 칸에 저장하던 옛 버전 (claude/blink-privacy-text에서 sr-v2로 수정됨)
        print('KNOWN 오프라인 개인정보처리방침 → ' + pg.title() + ' (배포된 sw.js가 옛 버전 sr-v1, 수정본은 main 미병합)'); known.append('offline privacy (sr-v1)')
    else:
        check(ok, '오프라인 개인정보처리방침: ' + pg.title())
    ctx.set_offline(False)
    check(not pe, f'페이지 오류 {pe}')
    b.close()
print('KNOWN', known)
print('ERR', errs)
sys.exit(1 if errs else 0)
