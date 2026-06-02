from __future__ import annotations
import math, torch
class AdamW(torch.optim.Optimizer):
    def __init__(self,params,lr=3e-4,betas=(0.9,0.95),eps=1e-8,weight_decay=0.1): super().__init__(params,dict(lr=lr,betas=betas,eps=eps,weight_decay=weight_decay))
    def step(self,closure=None):
        loss=None
        if closure is not None:
            with torch.enable_grad(): loss=closure()
        with torch.no_grad():
            for group in self.param_groups:
                lr=group['lr']; b1,b2=group['betas']; eps=group['eps']; wd=group['weight_decay']
                for p in group['params']:
                    if p.grad is None: continue
                    grad=p.grad; state=self.state[p]
                    if len(state)==0: state['step']=0; state['m']=torch.zeros_like(p); state['v']=torch.zeros_like(p)
                    state['step']+=1; m=state['m']; v=state['v']; p.mul_(1-lr*wd); m.mul_(b1).add_(grad,alpha=1-b1); v.mul_(b2).addcmul_(grad,grad,value=1-b2)
                    mh=m/(1-b1**state['step']); vh=v/(1-b2**state['step']); p.addcdiv_(mh, vh.sqrt().add_(eps), value=-lr)
        return loss

def cosine_lr(step,max_steps,warmup,base_lr,min_lr=0.0):
    if step < warmup: return base_lr*step/max(1,warmup)
    progress=min(1.0,max(0.0,(step-warmup)/max(1,max_steps-warmup)))
    return min_lr + 0.5*(base_lr-min_lr)*(1+math.cos(math.pi*progress))
