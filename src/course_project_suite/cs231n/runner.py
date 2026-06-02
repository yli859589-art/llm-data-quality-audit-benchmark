from __future__ import annotations
import numpy as np
from course_project_suite.common import CheckResult, make_classification, accuracy, set_seed, train_val_split
from .classifiers import KNearestNeighbor, TwoLayerNet
from .layers import conv_forward_naive, conv_backward_naive, batchnorm_forward, batchnorm_backward
from .sequence import rnn_step_forward, rnn_step_backward, attention_forward
from .diffusion_contrastive import q_sample, clip_contrastive_loss

def run():
    set_seed(3); X,y=make_classification(n=180,d=6,c=3,seed=7); X_train,X_val,y_train,y_val=train_val_split(X,y,val_fraction=.25,seed=7)
    knn=KNearestNeighbor(); knn.train(X_train,y_train); knn_acc=accuracy(knn.predict(X_val,k=3),y_val)
    net=TwoLayerNet(6,20,3,seed=5,reg=1e-3).train(X_train,y_train,epochs=250,lr=0.15); nn_acc=accuracy(net.predict(X_val),y_val)
    x=np.random.randn(2,1,5,5); w=np.random.randn(2,1,3,3)*0.1; b=np.zeros(2); out,cache=conv_forward_naive(x,w,b,{'stride':1,'pad':1}); dx,dw,db=conv_backward_naive(np.ones_like(out),cache)
    xb=np.random.randn(5,4); gamma=np.ones(4); beta=np.zeros(4); bo,bc=batchnorm_forward(xb,gamma,beta); bdx,_,_=batchnorm_backward(np.ones_like(bo),bc)
    q=np.random.randn(2,3,4); att,wts=attention_forward(q,q,q)
    qs,_=q_sample(np.random.randn(3,4),np.array([0,1,2])); cl=clip_contrastive_loss(np.random.randn(4,5),np.random.randn(4,5))
    metrics={'knn_val_acc':knn_acc,'two_layer_val_acc':nn_acc,'conv_shape':list(out.shape),'bn_dx_norm':float(np.linalg.norm(bdx)),'attention_shape':list(att.shape),'diffusion_shape':list(qs.shape),'clip_loss':cl}
    return CheckResult('cs231n_assignments_public_alignment', knn_acc>0.8 and nn_acc>0.9 and out.shape==(2,2,5,5) and np.isfinite(cl), metrics)
