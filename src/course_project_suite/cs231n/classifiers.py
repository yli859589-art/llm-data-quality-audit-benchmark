from __future__ import annotations
import numpy as np
from .layers import affine_forward, affine_backward, relu_forward, relu_backward, softmax_loss

class KNearestNeighbor:
    def train(self,X,y): self.X=X; self.y=y
    def predict(self,X,k=1):
        d=((X[:,None,:]-self.X[None,:,:])**2).sum(-1)
        idx=np.argsort(d,axis=1)[:,:k]
        return np.array([np.bincount(self.y[ii]).argmax() for ii in idx])

class TwoLayerNet:
    def __init__(self,input_dim,hidden_dim,num_classes,weight_scale=1e-1,reg=0.0,seed=0):
        rng=np.random.default_rng(seed); self.params={'W1':rng.normal(scale=weight_scale,size=(input_dim,hidden_dim)),'b1':np.zeros(hidden_dim),'W2':rng.normal(scale=weight_scale,size=(hidden_dim,num_classes)),'b2':np.zeros(num_classes)}; self.reg=reg
    def loss(self,X,y=None):
        a1,fc1=affine_forward(X,self.params['W1'],self.params['b1']); h1,rc=relu_forward(a1); scores,fc2=affine_forward(h1,self.params['W2'],self.params['b2'])
        if y is None: return scores
        loss,ds=softmax_loss(scores,y); loss += 0.5*self.reg*(np.sum(self.params['W1']**2)+np.sum(self.params['W2']**2))
        dh,dW2,db2=affine_backward(ds,fc2); da=relu_backward(dh,rc); dX,dW1,db1=affine_backward(da,fc1)
        grads={'W1':dW1+self.reg*self.params['W1'],'b1':db1,'W2':dW2+self.reg*self.params['W2'],'b2':db2}
        return loss,grads
    def train(self,X,y,lr=0.1,epochs=200):
        for _ in range(epochs):
            loss,grads=self.loss(X,y)
            for k in self.params: self.params[k]-=lr*grads[k]
        return self
    def predict(self,X): return np.argmax(self.loss(X),axis=1)
