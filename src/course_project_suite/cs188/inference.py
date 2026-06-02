from __future__ import annotations
import random, math
from collections import defaultdict

def normalize(dist):
    s=sum(dist.values())
    return {k:(v/s if s else 0.0) for k,v in dist.items()}

class DiscreteDistribution(defaultdict):
    def __init__(self,*a,**kw): super().__init__(float,*a,**kw)
    def normalize(self):
        nd=normalize(self); self.clear(); self.update(nd)
    def sample(self):
        total=sum(self.values()); r=random.random()*total; acc=0
        for k,v in self.items():
            acc+=v
            if acc>=r: return k
        return next(iter(self))

def forward_filter(observations, states, start_p, trans_p, emit_p):
    if not observations: return []
    belief=normalize({s:start_p.get(s,0.0)*emit_p[s].get(observations[0],0.0) for s in states})
    history=[belief]
    for observation in observations[1:]:
        belief=normalize({
            s:emit_p[s].get(observation,0.0)*sum(history[-1][sp]*trans_p[sp].get(s,0.0) for sp in states)
            for s in states
        })
        history.append(belief)
    return history

def viterbi(observations, states, start_p, trans_p, emit_p):
    V=[{}]; path={}
    for s in states:
        V[0][s]=math.log(start_p.get(s,1e-12))+math.log(emit_p[s].get(observations[0],1e-12)); path[s]=[s]
    for t in range(1,len(observations)):
        V.append({}); new_path={}
        for s in states:
            prob,prev=max((V[t-1][sp]+math.log(trans_p[sp].get(s,1e-12))+math.log(emit_p[s].get(observations[t],1e-12)),sp) for sp in states)
            V[t][s]=prob; new_path[s]=path[prev]+[s]
        path=new_path
    prob,state=max((V[-1][s],s) for s in states)
    return path[state], prob

class ParticleFilter:
    def __init__(self, states, transition_fn, observation_likelihood, num_particles=200):
        self.states=list(states); self.transition_fn=transition_fn; self.observation_likelihood=observation_likelihood; self.num_particles=num_particles
        self.particles=[random.choice(self.states) for _ in range(num_particles)]
    def observe(self, observation):
        weights=DiscreteDistribution()
        for p in self.particles: weights[p] += self.observation_likelihood(observation,p)
        if sum(weights.values()) == 0:
            self.particles=[random.choice(self.states) for _ in range(self.num_particles)]
        else:
            weights.normalize(); self.particles=[weights.sample() for _ in range(self.num_particles)]
    def elapse_time(self): self.particles=[self.transition_fn(p) for p in self.particles]
    def belief(self):
        b=DiscreteDistribution()
        for p in self.particles: b[p]+=1
        b.normalize(); return dict(b)
