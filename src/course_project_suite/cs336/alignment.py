from __future__ import annotations
import torch
import torch.nn.functional as F

def sft_loss(logits,targets,ignore_index=-100): return F.cross_entropy(logits.view(-1,logits.size(-1)),targets.reshape(-1),ignore_index=ignore_index)

def sequence_logprob(logits,targets):
    logp=F.log_softmax(logits,dim=-1); return torch.gather(logp,-1,targets.unsqueeze(-1)).squeeze(-1).sum(-1)

def dpo_loss(policy_chosen,policy_rejected,ref_chosen,ref_rejected,beta=0.1):
    logits=beta*((policy_chosen-policy_rejected)-(ref_chosen-ref_rejected)); return -F.logsigmoid(logits).mean()

def reward_weighted_loss(logprobs,rewards): return -(logprobs*rewards).mean()
