from __future__ import annotations
from collections import Counter

class BPETokenizer:
    def __init__(self): self.merges=[]; self.vocab={}
    def _word(self,w): return tuple(list(w)+['</w>'])
    def train(self,texts,num_merges=50):
        words=Counter()
        for text in texts:
            for w in text.strip().split(): words[self._word(w)] += 1
        for _ in range(num_merges):
            pairs=Counter()
            for word,c in words.items():
                for a,b in zip(word,word[1:]): pairs[(a,b)] += c
            if not pairs: break
            best=max(pairs,key=pairs.get); self.merges.append(best); new=Counter()
            for word,c in words.items():
                out=[]; i=0
                while i<len(word):
                    if i<len(word)-1 and (word[i],word[i+1])==best: out.append(word[i]+word[i+1]); i+=2
                    else: out.append(word[i]); i+=1
                new[tuple(out)] += c
            words=new
        toks=sorted({t for w in words for t in w} | {'<unk>'}); self.vocab={t:i for i,t in enumerate(toks)}; return self
    def encode_word(self,w):
        toks=list(w)+['</w>']
        for a,b in self.merges:
            out=[]; i=0
            while i<len(toks):
                if i<len(toks)-1 and toks[i]==a and toks[i+1]==b: out.append(a+b); i+=2
                else: out.append(toks[i]); i+=1
            toks=out
        return [self.vocab.get(t,self.vocab.get('<unk>',0)) for t in toks]
    def encode(self,text):
        ids=[]
        for w in text.split(): ids.extend(self.encode_word(w))
        return ids
    def decode(self,ids):
        inv={i:t for t,i in self.vocab.items()}; s=''.join(inv.get(i,'<unk>') for i in ids); return s.replace('</w>',' ').strip()
