import unicodedata, sys, importlib.util
def cnt(s): return sum(1 for ch in s if unicodedata.category(ch)[0] in 'LN')
# 글자 세기 규칙(원전 p.155: 제목부터, 띄어쓰기·문장부호 제외) 확인용 문장. 저작권 때문에 원전 본문 대신 자체 제작한 문장을 쓴다.
# 숫자는 줄마다의 누적 글자 수(한글 음절·숫자·영문만 따로 센 값과 일치 확인, 2026-11-19). 원전 표본과의 대조는 2026-10 작업 기록 참고.
# 줄머리 기호(□)는 세지 않고, 줄바꿈으로 나뉜 낱말("벗"/"어나야")은 이어 센다.
book=[("하루 10분씩 꾸준히 읽어도 읽는 힘은 자란다.",19),
      ("□ 읽는 속도를 알고 싶다면 1분 동안 몇 글자를 읽는지부터 재어 보자.",46),
      ("이 연습을 오래 이어 가려면 먼저 다음과 같은 두 가지 생각에서 벗",72),
      ("어나야 한다.",77),("첫째 생각은 내용을 모두 외워야만 제대로 읽은 것이라는 믿음이다.",104)]
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
