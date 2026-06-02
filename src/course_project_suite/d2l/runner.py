from __future__ import annotations
import numpy as np
from course_project_suite.common import CheckResult, make_classification, accuracy, set_seed, train_val_split
from .core import synthetic_data, linreg, softmax_regression_train, corr2d, dot_product_attention

def run():
    set_seed(4); X,y=synthetic_data([2,-3.4],4.2,80,seed=1); w=np.zeros(2); b=0.0
    for _ in range(100):
        pred=linreg(X,w,b); dw=X.T@(pred-y)/len(X); db=(pred-y).mean(); w-=0.1*dw; b-=0.1*db
    Xc,yc=make_classification(n=160,d=4,c=3,seed=8); X_train,X_val,y_train,y_val=train_val_split(Xc,yc,val_fraction=.25,seed=8)
    W,B=softmax_regression_train(X_train,y_train,3); acc=accuracy(np.argmax(X_val@W+B,axis=1),y_val)
    conv=corr2d(np.arange(9).reshape(3,3),np.array([[1,0],[0,-1]])); att,_=dot_product_attention(np.ones((2,1,3)),np.ones((2,4,3)),np.ones((2,4,5)),valid_lens=[2,3])
    metrics={'linreg_w_error':float(np.linalg.norm(w-np.array([2,-3.4]))),'linreg_b':float(b),'softmax_val_acc':acc,'conv_sum':float(conv.sum()),'attention_shape':list(att.shape)}
    return CheckResult('d2l_textbook_public_alignment', metrics['linreg_w_error']<0.08 and acc>0.9 and att.shape==(2,1,5), metrics)
