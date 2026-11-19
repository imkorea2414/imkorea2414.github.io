"""Build index.html from src/template.html + src/passages.json.
Usage (repo root): python3 tools/build.py
"""
import json, re, subprocess, pathlib, sys
root = pathlib.Path(__file__).resolve().parent.parent
s = (root / 'src/template.html').read_text(encoding='utf-8')
P = json.loads((root / 'src/passages.json').read_text(encoding='utf-8'))
out = s.replace('/*PASSAGES*/[]', json.dumps(P, ensure_ascii=False))
out = (out.replace('<title>Training Player 프로토타입 — Day 1</title>', '<title>속독 트레이닝</title>')
          .replace("title:'Training Player 프로토타입 — Day 1'", "title:'속독 트레이닝'")
          .replace("title:'Training Player prototype — Day 1'", "title:'Speed Reading Training'"))
(root / 'index.html').write_text(out, encoding='utf-8')
js = re.findall(r'<script>(.*?)</script>', out, re.S)[-1]
tmp = root / 'tools/.built.js'; tmp.write_text(js, encoding='utf-8')
r = subprocess.run(['node', '--check', str(tmp)], capture_output=True, text=True); tmp.unlink()
if r.returncode: print(r.stderr); sys.exit(1)
# 오프라인 글꼴 (설계): 앱이 보여 줄 수 있는 글자(index.html 안의 모든 글자)를 그리는 글꼴 조각 목록.
# 서비스 워커가 설치될 때 이 목록을 미리 저장한다 → 처음 설치한 날, 아직 열지 않은 화면도 오프라인에서 같은 글꼴로 보인다.
css = (root / 'fonts/fonts.css').read_text(encoding='utf-8')
chars = {ord(c) for c in out}
def hits(rng):
    for part in rng.split(','):
        a, _, b = part.strip()[2:].partition('-')
        lo = int(a, 16); hi = int(b, 16) if b else lo
        if any(lo <= c <= hi for c in chars): return True
    return False
pre = sorted(f for f, rng in re.findall(r"src: url\(([^)]+\.woff2)\)[^}]*?unicode-range: ([^;]+);", css) if hits(rng))
size = sum((root / 'fonts' / f).stat().st_size for f in pre)
(root / 'fonts/precache.json').write_text(json.dumps(pre, indent=0) + '\n', encoding='utf-8')
print(f'build ok -> index.html, fonts/precache.json ({len(pre)} files, {size/1e6:.2f} MB)')
