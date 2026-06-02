from __future__ import annotations
import numpy as np

def rnn_step_forward(x,prev_h,Wx,Wh,b):
    next_h=np.tanh(x@Wx+prev_h@Wh+b); return next_h,(x,prev_h,Wx,Wh,next_h)
def rnn_step_backward(dnext_h,cache):
    x,prev_h,Wx,Wh,next_h=cache; dt=dnext_h*(1-next_h**2); dx=dt@Wx.T; dprev=dt@Wh.T; dWx=x.T@dt; dWh=prev_h.T@dt; db=dt.sum(0); return dx,dprev,dWx,dWh,db

def attention_forward(q,k,v,mask=None):
    scores=q@k.swapaxes(-1,-2)/np.sqrt(q.shape[-1])
    if mask is not None: scores=np.where(mask,scores,-1e9)
    weights=np.exp(scores-scores.max(-1,keepdims=True)); weights/=weights.sum(-1,keepdims=True)
    return weights@v, weights

def temporal_softmax_loss(x,y,mask):
    N,T,V=x.shape; z=x.reshape(N*T,V); yy=y.reshape(N*T); mm=mask.reshape(N*T)
    z-=z.max(1,keepdims=True); p=np.exp(z); p/=p.sum(1,keepdims=True)
    loss=-np.sum(mm*np.log(p[np.arange(N*T),yy]+1e-12))/N
    dx=p; dx[np.arange(N*T),yy]-=1; dx/=N; dx*=mm[:,None]
    return loss,dx.reshape(N,T,V)
