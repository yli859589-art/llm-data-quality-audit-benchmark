from __future__ import annotations
import numpy as np, torch
from course_project_suite.common import CheckResult, set_seed
from .word_vectors import build_vocab, cooccurrence_matrix, ppmi, skipgram_negative_sampling_loss
from .parser import PartialParse
from .gpt2 import GPT2Config, MiniGPT2
from .tasks import rouge_l, paraphrase_features

def run():
    set_seed(5); corpus=[['i','like','nlp'],['i','like','deep','learning'],['nlp','uses','learning']]
    vocab,_=build_vocab(corpus); C=cooccurrence_matrix(corpus,vocab); P=ppmi(C)
    loss,_,_,_=skipgram_negative_sampling_loss(np.ones(4),np.ones(4)*.2,np.ones((3,4))*.1)
    pp=PartialParse(['parse','this']); deps=pp.parse(['S','S','RA','RA'])
    cfg=GPT2Config(vocab_size=64,block_size=8,n_layer=1,n_head=2,n_embd=16); model=MiniGPT2(cfg); idx=torch.randint(0,64,(2,8)); logits,lm_loss=model(idx,idx); gen=model.generate(idx[:1,:2],max_new_tokens=3)
    r=rouge_l('the cat sat','the cat sat down'); pf=paraphrase_features('a b c','a b d')
    metrics={'vocab':len(vocab),'ppmi_sum':float(P.sum()),'neg_sampling_loss':loss,'deps':len(deps),'logits_shape':list(logits.shape),'lm_loss':float(lm_loss.detach()),'gen_len':int(gen.shape[1]),'rouge_l':float(r),'paraphrase_jaccard':float(pf[0])}
    ok=P.shape[0]==len(vocab) and logits.shape==(2,8,64) and np.isfinite(loss) and len(deps)==2
    return CheckResult('cs224n_assignments_default_gpt2_public_alignment', ok, metrics)
