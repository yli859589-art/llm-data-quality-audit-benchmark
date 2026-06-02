from __future__ import annotations
import numpy as np
from course_project_suite.common import softmax

def cosine_beta_schedule(timesteps,s=0.008):
    steps=timesteps+1; x=np.linspace(0,timesteps,steps); alphas=np.cos(((x/timesteps)+s)/(1+s)*np.pi*0.5)**2; alphas=alphas/alphas[0]; betas=1-(alphas[1:]/alphas[:-1]); return np.clip(betas,1e-4,0.999)
def q_sample(x0,t,noise=None,betas=None):
    if betas is None: betas=cosine_beta_schedule(int(np.max(t))+1)
    if noise is None: noise=np.random.normal(size=x0.shape)
    alpha_bar=np.cumprod(1-betas)[t].reshape(-1,*([1]*(x0.ndim-1)))
    return np.sqrt(alpha_bar)*x0 + np.sqrt(1-alpha_bar)*noise, noise

def clip_contrastive_loss(image_features,text_features,temperature=0.07):
    im=image_features/np.linalg.norm(image_features,axis=1,keepdims=True); tx=text_features/np.linalg.norm(text_features,axis=1,keepdims=True)
    logits=im@tx.T/temperature; labels=np.arange(len(im)); p=softmax(logits,axis=1); q=softmax(logits.T,axis=1)
    return float((-np.log(p[labels,labels]+1e-12).mean()-np.log(q[labels,labels]+1e-12).mean())/2)

def dino_centered_softmax(student,teacher,center=None,temp_s=0.1,temp_t=0.04):
    center=0 if center is None else center
    ps=softmax(student/temp_s,axis=1); pt=softmax((teacher-center)/temp_t,axis=1)
    return float(-np.mean(np.sum(pt*np.log(ps+1e-12),axis=1)))
