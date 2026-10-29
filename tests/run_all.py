"""모든 시나리오 테스트를 실행하고 결과를 모아 보여 준다. 하나라도 실패하면 종료 코드 1.
사용: (저장소 루트에서 python3 -m http.server 8765 를 켠 상태)
  python3 tests/run_all.py            # Chromium
  BROWSER=webkit python3 tests/run_all.py
"""
import os, re, subprocess, sys, pathlib
here = pathlib.Path(__file__).resolve().parent
engine = os.environ.get('BROWSER', 'chromium')
failed = []
for t in sorted(here.glob('*test.py')):
    try:
        r = subprocess.run([sys.executable, t.name], cwd=here, capture_output=True, text=True, timeout=900, stdin=subprocess.DEVNULL)
        out = (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        out, r = 'TIMEOUT', None
    last = out.splitlines()[-1] if out else ''
    ok = r is not None and r.returncode == 0 and re.search(r'ERR(ORS)? \[\]$', last)
    print(f'{engine:8} {t.name:20} {"ok" if ok else "FAIL"}', flush=True)
    if not ok:
        failed.append(t.name); print('\n'.join(out.splitlines()[-25:]), flush=True)
print('failed:', failed or 'none')
sys.exit(1 if failed else 0)
