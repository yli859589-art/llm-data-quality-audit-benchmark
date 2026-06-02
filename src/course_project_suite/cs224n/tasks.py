from __future__ import annotations
import numpy as np

def lcs_len(a,b):
    dp=np.zeros((len(a)+1,len(b)+1),dtype=int)
    for i,x in enumerate(a,1):
        for j,y in enumerate(b,1): dp[i,j]=dp[i-1,j-1]+1 if x==y else max(dp[i-1,j],dp[i,j-1])
    return int(dp[-1,-1])
def rouge_l(pred,ref):
    p=pred.split(); r=ref.split(); l=lcs_len(p,r); prec=l/(len(p) or 1); rec=l/(len(r) or 1); return 2*prec*rec/(prec+rec+1e-12)
def paraphrase_features(a,b):
    A=set(a.lower().split()); B=set(b.lower().split()); return np.array([len(A&B)/(len(A|B) or 1), abs(len(A)-len(B)), int(A==B)],dtype=float)
