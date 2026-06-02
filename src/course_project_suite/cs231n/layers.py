from __future__ import annotations
import numpy as np

def affine_forward(x,w,b):
    out=x.reshape(x.shape[0],-1)@w+b; return out,(x,w,b)
def affine_backward(dout,cache):
    x,w,b=cache; xr=x.reshape(x.shape[0],-1)
    dx=(dout@w.T).reshape(x.shape); dw=xr.T@dout; db=dout.sum(0); return dx,dw,db

def relu_forward(x): return np.maximum(0,x),x
def relu_backward(dout,cache): return dout*(cache>0)

def svm_loss(x,y):
    N=x.shape[0]; correct=x[np.arange(N),y][:,None]; margins=np.maximum(0,x-correct+1); margins[np.arange(N),y]=0
    loss=margins.sum()/N; dx=(margins>0).astype(float); dx[np.arange(N),y]-=dx.sum(1); dx/=N; return loss,dx

def softmax_loss(x,y):
    shifted=x-x.max(1,keepdims=True); exp=np.exp(shifted); p=exp/exp.sum(1,keepdims=True); N=x.shape[0]
    loss=-np.log(p[np.arange(N),y]+1e-12).mean(); dx=p; dx[np.arange(N),y]-=1; dx/=N; return loss,dx

def batchnorm_forward(x,gamma,beta,eps=1e-5):
    mu=x.mean(0); var=x.var(0); xhat=(x-mu)/np.sqrt(var+eps); out=gamma*xhat+beta; return out,(x,xhat,mu,var,gamma,beta,eps)
def batchnorm_backward(dout,cache):
    x,xhat,mu,var,gamma,beta,eps=cache; N=x.shape[0]; ivar=1/np.sqrt(var+eps)
    dbeta=dout.sum(0); dgamma=np.sum(dout*xhat,0); dxhat=dout*gamma
    dx=(1/N)*ivar*(N*dxhat - dxhat.sum(0) - xhat*np.sum(dxhat*xhat,0)); return dx,dgamma,dbeta

def dropout_forward(x,p=0.5,seed=None,train=True):
    rng=np.random.default_rng(seed); mask=(rng.random(x.shape)>=p)/(1-p) if train else np.ones_like(x); return x*mask,(mask,train)
def dropout_backward(dout,cache): mask,train=cache; return dout*mask if train else dout

def conv_forward_naive(x,w,b,conv_param):
    stride=conv_param.get('stride',1); pad=conv_param.get('pad',0); N,C,H,W=x.shape; F,_,HH,WW=w.shape
    xp=np.pad(x,((0,0),(0,0),(pad,pad),(pad,pad))); Ho=1+(H+2*pad-HH)//stride; Wo=1+(W+2*pad-WW)//stride; out=np.zeros((N,F,Ho,Wo))
    for n in range(N):
      for f in range(F):
       for i in range(Ho):
        for j in range(Wo):
         region=xp[n,:,i*stride:i*stride+HH,j*stride:j*stride+WW]; out[n,f,i,j]=np.sum(region*w[f])+b[f]
    return out,(x,w,b,conv_param,xp)

def conv_backward_naive(dout,cache):
    x,w,b,conv_param,xp=cache; stride=conv_param.get('stride',1); pad=conv_param.get('pad',0); N,C,H,W=x.shape; F,_,HH,WW=w.shape; _,_,Ho,Wo=dout.shape
    dxp=np.zeros_like(xp); dw=np.zeros_like(w); db=dout.sum((0,2,3))
    for n in range(N):
      for f in range(F):
       for i in range(Ho):
        for j in range(Wo):
         region=xp[n,:,i*stride:i*stride+HH,j*stride:j*stride+WW]
         dw[f]+=dout[n,f,i,j]*region; dxp[n,:,i*stride:i*stride+HH,j*stride:j*stride+WW]+=dout[n,f,i,j]*w[f]
    dx=dxp[:,:,pad:pad+H,pad:pad+W] if pad else dxp
    return dx,dw,db

def max_pool_forward_naive(x,pool_param):
    ph=pool_param.get('pool_height',2); pw=pool_param.get('pool_width',2); stride=pool_param.get('stride',2); N,C,H,W=x.shape; Ho=1+(H-ph)//stride; Wo=1+(W-pw)//stride; out=np.zeros((N,C,Ho,Wo))
    for n in range(N):
     for c in range(C):
      for i in range(Ho):
       for j in range(Wo): out[n,c,i,j]=np.max(x[n,c,i*stride:i*stride+ph,j*stride:j*stride+pw])
    return out,(x,pool_param)

def max_pool_backward_naive(dout,cache):
    x,pool_param=cache; ph=pool_param.get('pool_height',2); pw=pool_param.get('pool_width',2); stride=pool_param.get('stride',2); N,C,Ho,Wo=dout.shape; dx=np.zeros_like(x)
    for n in range(N):
     for c in range(C):
      for i in range(Ho):
       for j in range(Wo):
        reg=x[n,c,i*stride:i*stride+ph,j*stride:j*stride+pw]; m=(reg==reg.max()); dx[n,c,i*stride:i*stride+ph,j*stride:j*stride+pw]+=dout[n,c,i,j]*m/m.sum()
    return dx
