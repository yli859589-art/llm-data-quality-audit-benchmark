from __future__ import annotations
import numpy as np
from collections import Counter, defaultdict

def build_vocab(corpus,min_count=1):
    cnt=Counter(tok for sent in corpus for tok in sent); vocab={w:i for i,(w,c) in enumerate(cnt.items()) if c>=min_count}; return vocab,cnt

def cooccurrence_matrix(corpus,vocab,window=2):
    C=np.zeros((len(vocab),len(vocab)))
    for sent in corpus:
        for i,w in enumerate(sent):
            if w not in vocab: continue
            wi=vocab[w]
            for j in range(max(0,i-window),min(len(sent),i+window+1)):
                if i!=j and sent[j] in vocab: C[wi,vocab[sent[j]]]+=1
    return C

def ppmi(C):
    total=C.sum(); row=C.sum(1,keepdims=True); col=C.sum(0,keepdims=True); pmi=np.log((C*total+1e-12)/(row@col+1e-12)); return np.maximum(pmi,0)

def skipgram_negative_sampling_loss(center_vec,outside_vec,neg_vecs):
    def sig(x): return 1/(1+np.exp(-x))
    pos=center_vec@outside_vec; neg=neg_vecs@center_vec
    loss=-np.log(sig(pos)+1e-12)-np.sum(np.log(sig(-neg)+1e-12))
    grad_center=(sig(pos)-1)*outside_vec + (sig(neg)[:,None]*neg_vecs).sum(0)
    grad_out=(sig(pos)-1)*center_vec; grad_neg=sig(neg)[:,None]*center_vec
    return float(loss),grad_center,grad_out,grad_neg
