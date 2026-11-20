"""공개 배포 없이 실기기에서 최신 웹 앱을 확인하기 위한 로컬 서버 (개발 도구).

GitHub Pages에 올라가는 것과 같은 서비스 파일만 임시 폴더에 모아 이 컴퓨터에서만 띄운다
(개발 문서·테스트·원본은 보이지 않는다). 공개 주소는 만들지 않는다.

사용 (저장소 루트, Python 3.8 이상, 추가 설치 없음):
  python3 tools/build.py              # 먼저 빌드 (index.html, fonts/precache.json 최신으로)
  python3 tools/serve_local.py        # http://localhost:8765 (이 컴퓨터에서만 접속)
  python3 tools/serve_local.py --lan  # 같은 Wi-Fi의 기기에서 http://<이 컴퓨터 IP>:8765 (제약 많음, 아래)

Android 휴대폰은 USB로 연결하고 데스크톱 Chrome의 chrome://inspect → Port forwarding에서
8765 → localhost:8765 를 켜면, 휴대폰 Chrome에서 http://localhost:8765 가 이 서버로 연결된다.
localhost는 "보안 출처"라 서비스 워커(오프라인)·화면 켜짐 유지가 공개 사이트와 같게 동작한다.
--lan(http://IP)은 보안 출처가 아니라 서비스 워커·오프라인·화면 켜짐 유지가 동작하지 않는다.

오프라인 확인: 서버를 Ctrl+C로 멈추면 휴대폰에서는 "인터넷이 끊긴 것"과 같다 (USB 연결은 그대로 두어도 됨).
localhost:8765의 기록은 공개 사이트(imkorea2414.github.io)·설치한 앱의 기록과 따로 저장된다 (주소가 다르므로).
"""
import argparse, functools, http.server, pathlib, shutil, socket, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
# .github/workflows/pages.yml 의 FILES 와 같게 유지한다
FILES = ['index.html', 'privacy.html', 'manifest.webmanifest', 'sw.js',
         'icons/apple-touch-icon.png', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/maskable-512.png',
         '.well-known/assetlinks.json']

def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1)); return s.getsockname()[0]   # 실제로 보내지 않음, 경로만 확인
    except OSError:
        return '이 컴퓨터의 IP'
    finally:
        s.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--lan', action='store_true', help='같은 네트워크의 다른 기기에서도 접속 허용 (보안 출처 아님)')
    a = ap.parse_args()
    site = pathlib.Path(tempfile.mkdtemp(prefix='speedread-site-'))
    for f in FILES:
        (site / f).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT / f, site / f)
    shutil.copytree(ROOT / 'fonts', site / 'fonts')
    host = '0.0.0.0' if a.lan else '127.0.0.1'

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *x): pass
    with http.server.ThreadingHTTPServer((host, a.port), functools.partial(Handler, directory=str(site))) as srv:
        print(f'서비스 파일 {len(FILES)}개 + fonts/ 를 띄웠습니다: {site}')
        print(f'  이 컴퓨터:  http://localhost:{a.port}/')
        if a.lan:
            print(f'  같은 Wi-Fi: http://{lan_ip()}:{a.port}/  (보안 출처 아님: 오프라인·화면 켜짐 유지 확인 불가)')
        else:
            print(f'  Android: USB 연결 → 데스크톱 Chrome chrome://inspect → Port forwarding {a.port} → localhost:{a.port}')
        print('멈추기: Ctrl+C (멈추면 기기에서는 오프라인과 같음)')
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
    shutil.rmtree(site, ignore_errors=True)

if __name__ == '__main__':
    sys.exit(main())
