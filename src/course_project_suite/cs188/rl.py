from __future__ import annotations
import random, math
from collections import defaultdict

class GridMDP:
    def __init__(self, width=4, height=3, walls={(1,1)}, terminals={(3,0):1.0,(3,1):-1.0}, living_reward=-0.04, noise=0.2):
        self.width=width; self.height=height; self.walls=set(walls); self.terminals=dict(terminals); self.living_reward=living_reward; self.noise=noise
    def states(self): return [(x,y) for y in range(self.height) for x in range(self.width) if (x,y) not in self.walls]
    def actions(self, s): return [] if s in self.terminals else ['North','South','East','West']
    def move(self,s,a):
        d={'North':(0,-1),'South':(0,1),'East':(1,0),'West':(-1,0)}[a]
        ns=(s[0]+d[0],s[1]+d[1])
        return s if ns[0]<0 or ns[0]>=self.width or ns[1]<0 or ns[1]>=self.height or ns in self.walls else ns
    def transitions(self,s,a):
        if s in self.terminals: return []
        left={'North':'West','South':'East','East':'North','West':'South'}[a]
        right={'North':'East','South':'West','East':'South','West':'North'}[a]
        probs=defaultdict(float)
        for act,p in [(a,1-self.noise),(left,self.noise/2),(right,self.noise/2)]: probs[self.move(s,act)] += p
        return list(probs.items())
    def reward(self,s,a,ns): return self.terminals.get(ns,self.living_reward)

def value_iteration(mdp: GridMDP, gamma=0.9, iterations=100):
    V={s:0.0 for s in mdp.states()}
    for _ in range(iterations):
        new=V.copy()
        for s in mdp.states():
            acts=mdp.actions(s)
            if acts:
                new[s]=max(sum(p*(mdp.reward(s,a,ns)+gamma*V[ns]) for ns,p in mdp.transitions(s,a)) for a in acts)
        V=new
    policy={}
    for s in mdp.states():
        acts=mdp.actions(s)
        if acts:
            policy[s]=max(acts, key=lambda a: sum(p*(mdp.reward(s,a,ns)+gamma*V[ns]) for ns,p in mdp.transitions(s,a)))
    return V, policy

class QLearningAgent:
    def __init__(self, actions, alpha=0.5, epsilon=0.1, gamma=0.9):
        self.actions=list(actions); self.alpha=alpha; self.epsilon=epsilon; self.gamma=gamma; self.Q=defaultdict(float)
    def get_q_value(self,s,a): return self.Q[(s,a)]
    def value(self,s): return max([self.get_q_value(s,a) for a in self.actions] or [0.0])
    def policy(self,s): return max(self.actions, key=lambda a:self.get_q_value(s,a))
    def action(self,s): return random.choice(self.actions) if random.random()<self.epsilon else self.policy(s)
    def update(self,s,a,ns,r): self.Q[(s,a)] += self.alpha*(r + self.gamma*self.value(ns) - self.Q[(s,a)])

class ApproximateQAgent(QLearningAgent):
    def __init__(self, actions, feature_fn, **kw):
        super().__init__(actions, **kw); self.feature_fn=feature_fn; self.weights=defaultdict(float)
    def get_q_value(self,s,a): return sum(self.weights[f]*v for f,v in self.feature_fn(s,a).items())
    def update(self,s,a,ns,r):
        diff = r + self.gamma*self.value(ns) - self.get_q_value(s,a)
        for f,v in self.feature_fn(s,a).items(): self.weights[f] += self.alpha*diff*v
