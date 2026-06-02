from __future__ import annotations
import numpy as np, torch
from course_project_suite.common import CheckResult, set_seed
from .tokenizer import BPETokenizer
from .systems import benchmark_attention, estimate_activation_memory, naive_attention, online_attention
from .scaling import fit_scaling_law, predict_loss
from .data import clean_common_crawl_text, quality_filter, exact_deduplicate, redact_pii
from .alignment import dpo_loss, sft_loss
from .optim import AdamW, cosine_lr
from course_project_suite.cs224n.gpt2 import GPT2Config, MiniGPT2

def run():
    set_seed(6)
    tok=BPETokenizer().train(['language models from scratch','language modeling systems scaling data alignment'],num_merges=20); ids=tok.encode('language models')
    cfg=GPT2Config(vocab_size=max(128,len(tok.vocab)+5),block_size=8,n_layer=1,n_head=2,n_embd=16); model=MiniGPT2(cfg); x=torch.randint(0,cfg.vocab_size,(2,8)); logits,loss=model(x,x); opt=AdamW(model.parameters(),lr=1e-3,weight_decay=0.01); loss.backward(); opt.step()
    bench=benchmark_attention(T=16,D=8,repeats=1)
    fit=fit_scaling_law(np.array([1e6,2e6,4e6]),np.array([1e8,2e8,4e8]),np.array([4.0,3.2,2.6])); pred=predict_loss(fit,3e6,3e8)
    txt=redact_pii(clean_common_crawl_text('<p>Email me a@b.com about language models.</p>')); quality=quality_filter(txt,min_words=3); dedup=exact_deduplicate([txt,txt,'another clean language document here'])
    dl=dpo_loss(torch.tensor([1.2,1.0]),torch.tensor([0.2,0.4]),torch.tensor([0.8,0.6]),torch.tensor([0.5,0.4]))
    metrics={'bpe_vocab':len(tok.vocab),'encoded_len':len(ids),'lm_loss':float(loss.detach()),'attention_diff':bench['max_diff'],'scaling_pred':float(pred),'quality':quality,'dedup_count':len(dedup),'dpo_loss':float(dl.detach()),'activation_memory':estimate_activation_memory(2,8,2,16),'cosine_lr_10':cosine_lr(10,100,5,1e-3)}
    ok=len(ids)>0 and float(loss.detach())>0 and bench['max_diff']<1e-5 and quality and len(dedup)==2 and metrics['dpo_loss']>0
    return CheckResult('cs336_language_modeling_from_scratch_public_alignment', ok, metrics)
