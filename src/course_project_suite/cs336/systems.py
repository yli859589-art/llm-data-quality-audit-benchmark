from __future__ import annotations
import time, math, torch
import torch.nn.functional as F

def naive_attention(q,k,v,causal=True):
    att=q@k.transpose(-2,-1)/math.sqrt(q.size(-1))
    if causal:
        T=q.size(-2); mask=torch.tril(torch.ones(T,T,device=q.device,dtype=torch.bool)); att=att.masked_fill(~mask,float('-inf'))
    return F.softmax(att,dim=-1)@v

def torch_sdpa_attention(q,k,v,causal=True):
    return F.scaled_dot_product_attention(q,k,v,is_causal=causal)

def online_attention(q,k,v):
    # numerically stable reference for one batch/head
    scores=q@k.transpose(-2,-1)/math.sqrt(q.size(-1)); scores=scores.masked_fill(~torch.tril(torch.ones(scores.shape[-2:],device=q.device,dtype=torch.bool)),float('-inf'))
    m=scores.max(dim=-1,keepdim=True).values; p=torch.exp(scores-m); return (p@v)/p.sum(dim=-1,keepdim=True)

def benchmark_attention(device='cpu',T=32,D=16,repeats=3):
    q=torch.randn(1,2,T,D,device=device); k=torch.randn_like(q); v=torch.randn_like(q)
    start=time.perf_counter()
    for _ in range(repeats): y=naive_attention(q,k,v)
    naive=time.perf_counter()-start
    start=time.perf_counter()
    for _ in range(repeats): z=torch_sdpa_attention(q,k,v)
    sdpa=time.perf_counter()-start
    return {'naive_seconds':naive,'sdpa_seconds':sdpa,'max_diff':float((y-z).abs().max())}

def estimate_activation_memory(batch,seq,n_layer,n_embd,bytes_per=4): return batch*seq*n_layer*n_embd*bytes_per*6
