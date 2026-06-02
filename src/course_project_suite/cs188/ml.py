from __future__ import annotations
import numpy as np
from course_project_suite.common import softmax, one_hot

class PerceptronClassifier:
    def __init__(self, num_features, num_classes, lr=1.0, epochs=10):
        self.W=np.zeros((num_features,num_classes)); self.lr=lr; self.epochs=epochs
    def fit(self,X,y):
        for _ in range(self.epochs):
            for xi,yi in zip(X,y):
                pred=int(np.argmax(xi@self.W))
                if pred != yi:
                    self.W[:,yi]+=self.lr*xi; self.W[:,pred]-=self.lr*xi
        return self
    def predict(self,X): return np.argmax(X@self.W,axis=1)

class NumpyMLP:
    def __init__(self,d,h,c,seed=0):
        rng=np.random.default_rng(seed); self.W1=rng.normal(scale=0.1,size=(d,h)); self.b1=np.zeros(h); self.W2=rng.normal(scale=0.1,size=(h,c)); self.b2=np.zeros(c)
    def fit(self,X,y,lr=0.2,epochs=100):
        Y=one_hot(y,self.b2.size)
        for _ in range(epochs):
            z1=X@self.W1+self.b1; h=np.maximum(0,z1); scores=h@self.W2+self.b2; p=softmax(scores,axis=1)
            ds=(p-Y)/len(X); dW2=h.T@ds; db2=ds.sum(0); dh=ds@self.W2.T; dz=dh*(z1>0); dW1=X.T@dz; db1=dz.sum(0)
            self.W1-=lr*dW1; self.b1-=lr*db1; self.W2-=lr*dW2; self.b2-=lr*db2
        return self
    def predict(self,X): return np.argmax(np.maximum(0,X@self.W1+self.b1)@self.W2+self.b2,axis=1)
