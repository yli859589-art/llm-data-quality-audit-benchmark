from __future__ import annotations
import numpy as np

def fit_scaling_law(params,tokens,losses):
    X=np.c_[np.ones(len(losses)), np.log(params), np.log(tokens)]
    y=np.log(losses)
    coef=np.linalg.lstsq(X,y,rcond=None)[0]
    return {'A':float(np.exp(coef[0])),'alpha':float(-coef[1]),'beta':float(-coef[2])}

def predict_loss(fit,params,tokens): return fit['A']*(params**(-fit['alpha']))*(tokens**(-fit['beta']))
