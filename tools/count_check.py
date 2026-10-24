import unicodedata, sys, importlib.util
def cnt(s): return sum(1 for ch in s if unicodedata.category(ch)[0] in 'LN')
book=[("1분에 1만자를 읽을 수도 있다.",13),
      ("□ 독서 능력을 높이려면 1분에 1만자씩 읽을 수 있는 훈련도 필요하다.",41),
      ("이 훈련을 실현시키기 위해서는 우선 다음과 같은 두 진술의 주장에서 벗",70),
      ("어나야 한다.",75),("벗어나야 할 첫째 주장은 학습 내용 중심 지향의 독서 전략이다.",100)]
c=0
for s,cum in book:
    c+=cnt(s); print('book', c, cum, 'OK' if c==cum else 'MISMATCH')
spec=importlib.util.spec_from_file_location('p', sys.argv[1]); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for p in m.PASSAGES:
    full=p['title']+'\n'+'\n'.join(p['paras'])
    unit = cnt(full) if p['lang']=='ko' else sum(1 for w in full.split() if any(unicodedata.category(ch)[0] in 'LN' for ch in w))
    pos=[]
    for q in p['qs']:
        i=full.find(q['at'])
        if i<0: pos.append('MISSING:'+q['at']); continue
        upto=full[:i+len(q['at'])]
        pos.append(cnt(upto) if p['lang']=='ko' else len(upto.split()))
    print(p['id'], 'total', unit, 'anchors', pos)
