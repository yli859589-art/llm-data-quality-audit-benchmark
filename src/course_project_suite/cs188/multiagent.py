from __future__ import annotations
import math, random
from .pacman_core import PacmanState

def score_evaluation_function(state: PacmanState): return state.score

def better_evaluation_function(state: PacmanState):
    if state.is_win(): return 1e6 + state.score
    if state.is_lose(): return -1e6 + state.score
    px,py=state.pacman
    food_d=[abs(px-x)+abs(py-y) for x,y in state.food]
    ghost_d=[abs(px-x)+abs(py-y) for x,y in state.ghosts]
    return state.score + (5.0/(min(food_d)+1) if food_d else 100) - (8.0/(min(ghost_d)+1) if ghost_d else 0) - 0.3*len(state.food)

class MultiAgentSearchAgent:
    def __init__(self, depth=2, eval_fn=better_evaluation_function):
        self.depth=depth; self.evaluation_function=eval_fn

class MinimaxAgent(MultiAgentSearchAgent):
    def get_action(self, state: PacmanState):
        def value(s, agent, ply):
            if s.is_win() or s.is_lose() or ply == self.depth:
                return self.evaluation_function(s)
            actions=s.legal_actions(agent)
            if agent == 0:
                return max(value(s.generate_successor(agent,a),1,ply) for a in actions)
            nxt_agent=0 if agent == s.num_agents()-1 else agent+1
            nxt_ply=ply+1 if nxt_agent == 0 else ply
            return min(value(s.generate_successor(agent,a),nxt_agent,nxt_ply) for a in actions)
        vals=[(value(state.generate_successor(0,a),1,0),a) for a in state.legal_actions(0)]
        return max(vals)[1]

class AlphaBetaAgent(MultiAgentSearchAgent):
    def get_action(self, state: PacmanState):
        def value(s, agent, ply, alpha, beta):
            if s.is_win() or s.is_lose() or ply == self.depth:
                return self.evaluation_function(s)
            actions=s.legal_actions(agent)
            if agent == 0:
                v=-math.inf
                for a in actions:
                    v=max(v, value(s.generate_successor(agent,a),1,ply,alpha,beta))
                    if v > beta: return v
                    alpha=max(alpha,v)
                return v
            v=math.inf; nxt_agent=lambda: 0 if agent == s.num_agents()-1 else agent+1
            for a in actions:
                na=nxt_agent(); np=ply+1 if na == 0 else ply
                v=min(v, value(s.generate_successor(agent,a),na,np,alpha,beta))
                if v < alpha: return v
                beta=min(beta,v)
            return v
        best=(-math.inf,None); alpha=-math.inf; beta=math.inf
        for a in state.legal_actions(0):
            v=value(state.generate_successor(0,a),1,0,alpha,beta)
            if v > best[0]: best=(v,a)
            alpha=max(alpha,v)
        return best[1]

class ExpectimaxAgent(MultiAgentSearchAgent):
    def get_action(self, state: PacmanState):
        def value(s, agent, ply):
            if s.is_win() or s.is_lose() or ply == self.depth: return self.evaluation_function(s)
            actions=s.legal_actions(agent)
            if agent == 0:
                return max(value(s.generate_successor(0,a),1,ply) for a in actions)
            na=0 if agent == s.num_agents()-1 else agent+1
            np=ply+1 if na == 0 else ply
            vals=[value(s.generate_successor(agent,a),na,np) for a in actions]
            return sum(vals)/len(vals)
        return max((value(state.generate_successor(0,a),1,0),a) for a in state.legal_actions(0))[1]
