import json, re, math
NARR="work/tts"
words=json.load(open(f"{NARR}/words.json")); words={int(k):v for k,v in words.items()}
CARDS={
 0:["태어난 순간 병원이","아이의 수명부터 정해줬습니다"],
 1:["부모는 사랑으로","아이를 가졌지만","세상은 유전자로","사람을 걸렀습니다"],
 3:["부모는 다음 아이만큼은","실험실에서 고르기로 했습니다","완벽하게 설계된","동생 안톤이었죠"],
 4:["형이 동생을","이겨볼 수 있는 곳은","바다뿐이었습니다","유전자로는 이미","진 승부였지만","물에서는 누가","먼저 겁먹는지로 겨뤘거든요","먼저 돌아서는 쪽이 지는 겁니다","지는 쪽은 언제나 형이었죠"],
 6:["형은 우주에 가고 싶었습니다","부모의 대답은 이랬죠"],
 8:["그러던 어느 날 동생이","마지막 시합을 걸어왔습니다"],
 10:["그런데 그날은 달랐습니다","동생이 아무리 앞서 나가려 해도","형이 계속 옆에 붙어 있었죠"],
 11:["먼저 가라앉은 건 동생이었고","형이 그를 끌고","뭍으로 나왔습니다","그날 형은 자기가","약하지 않다는 걸 알았습니다"],
 12:["어른이 된 형은","남의 인생을 통째로 빌립니다","돈이 필요했던 남자와","거래한 거죠"],
 13:["완벽한 유전자를 타고났지만","사고로 다리를 쓰지","못하게 된 남자였죠","형은 그의 피와 소변","머리카락을 매일","몸에 붙이고 출근했습니다"],
 14:["키까지 맞춰야 했습니다","양쪽 다리를 부러뜨려","늘리는 수술이었죠"],
 15:["그렇게 그는","우주 회사에 들어갔고","토성의 위성으로 떠나는","비행사로 뽑혔습니다"],
 16:["출발을 코앞에 두고","회사 간부가 살해당했습니다","현장에 떨어진","속눈썹 하나가","하필 형의 것이었죠"],
 17:["수사를 맡은 형사는","놀랍게도 그 동생이었습니다"],
 22:["진범은 따로 잡혔지만","동생은 형을 놓아주지 않았습니다","동생에게 형은","여전히 구해줘야 할","사람이었거든요"],
 20:["형제는 다시","바다로 들어갔습니다"],
}
def clean(s): return re.sub(r"[ ,.!?']","",s)
def align(bi):
    ws=words[bi]; cards=CARDS[bi]
    targets=[]; cum=0
    for c in cards: cum+=len(clean(c)); targets.append(cum)
    out=[]; wi=0; consumed=0
    for ci,tg in enumerate(targets):
        st=ws[wi][1]
        while wi<len(ws):
            nxt=consumed+len(clean(ws[wi][0]))
            if not (abs(nxt-tg)<=abs(consumed-tg) or nxt<=tg): break
            consumed=nxt; wi+=1
            if consumed>=tg: break
        out.append([cards[ci], st, ws[wi-1][2]])
    assert wi==len(ws), f"b{bi} 어절 잔여 {len(ws)-wi}: {[w[0] for w in ws[wi:]]}"
    return out
if __name__=="__main__":
    secs=json.load(open(f"{NARR}/secs.json")); secs={int(k):v for k,v in secs.items()}
    n=0
    for bi in sorted(CARDS):
        print(f"--- b{bi} ({secs[bi]}s)")
        for t,s,e in align(bi): print(f"   {s:6.2f}~{e:6.2f}  {t}"); n+=1
    print("카드 총", n, "장 / 나레 총", round(sum(secs.values()),2),"초")
