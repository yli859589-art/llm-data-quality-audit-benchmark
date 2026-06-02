from __future__ import annotations
from dataclasses import dataclass
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

@dataclass
class GPT2Config:
    vocab_size:int=128
    block_size:int=32
    n_layer:int=2
    n_head:int=2
    n_embd:int=64
    dropout:float=0.0

class CausalSelfAttention(nn.Module):
    def __init__(self,cfg:GPT2Config):
        super().__init__(); assert cfg.n_embd%cfg.n_head==0; self.n_head=cfg.n_head; self.head_dim=cfg.n_embd//cfg.n_head
        self.c_attn=nn.Linear(cfg.n_embd,3*cfg.n_embd); self.c_proj=nn.Linear(cfg.n_embd,cfg.n_embd); self.resid_dropout=nn.Dropout(cfg.dropout); self.register_buffer('bias',torch.tril(torch.ones(cfg.block_size,cfg.block_size)).view(1,1,cfg.block_size,cfg.block_size))
    def forward(self,x):
        B,T,C=x.size(); q,k,v=self.c_attn(x).split(C,dim=2)
        q=q.view(B,T,self.n_head,self.head_dim).transpose(1,2); k=k.view(B,T,self.n_head,self.head_dim).transpose(1,2); v=v.view(B,T,self.n_head,self.head_dim).transpose(1,2)
        att=(q@k.transpose(-2,-1))/math.sqrt(k.size(-1)); att=att.masked_fill(self.bias[:,:,:T,:T]==0,float('-inf')); att=F.softmax(att,dim=-1)
        y=(att@v).transpose(1,2).contiguous().view(B,T,C)
        return self.resid_dropout(self.c_proj(y))

class Block(nn.Module):
    def __init__(self,cfg):
        super().__init__(); self.ln_1=nn.LayerNorm(cfg.n_embd); self.attn=CausalSelfAttention(cfg); self.ln_2=nn.LayerNorm(cfg.n_embd); self.mlp=nn.Sequential(nn.Linear(cfg.n_embd,4*cfg.n_embd),nn.GELU(),nn.Linear(4*cfg.n_embd,cfg.n_embd),nn.Dropout(cfg.dropout))
    def forward(self,x): x=x+self.attn(self.ln_1(x)); return x+self.mlp(self.ln_2(x))

class MiniGPT2(nn.Module):
    def __init__(self,cfg:GPT2Config):
        super().__init__(); self.cfg=cfg; self.wte=nn.Embedding(cfg.vocab_size,cfg.n_embd); self.wpe=nn.Embedding(cfg.block_size,cfg.n_embd); self.drop=nn.Dropout(cfg.dropout); self.h=nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)]); self.ln_f=nn.LayerNorm(cfg.n_embd); self.lm_head=nn.Linear(cfg.n_embd,cfg.vocab_size,bias=False); self.lm_head.weight=self.wte.weight
    def forward(self,idx,targets=None):
        B,T=idx.shape; pos=torch.arange(T,device=idx.device); x=self.drop(self.wte(idx)+self.wpe(pos))
        for block in self.h: x=block(x)
        logits=self.lm_head(self.ln_f(x)); loss=None
        if targets is not None: loss=F.cross_entropy(logits.view(-1,logits.size(-1)),targets.reshape(-1))
        return logits,loss
    @torch.no_grad()
    def generate(self,idx,max_new_tokens=20,temperature=1.0):
        for _ in range(max_new_tokens):
            idx_cond=idx[:,-self.cfg.block_size:]; logits,_=self(idx_cond); logits=logits[:,-1,:]/temperature; probs=F.softmax(logits,dim=-1); nxt=torch.multinomial(probs,1); idx=torch.cat([idx,nxt],dim=1)
        return idx

def make_prediction_csv(path,ids,preds):
    import csv
    with open(path,'w',newline='') as f:
        wr=csv.writer(f); wr.writerow(['id','Predicted'])
        for i,p in zip(ids,preds): wr.writerow([i,p])
