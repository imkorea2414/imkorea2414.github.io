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
print('build ok -> index.html')
