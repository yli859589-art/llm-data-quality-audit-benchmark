from __future__ import annotations
from dataclasses import dataclass
import heapq
from collections import deque
from .pacman_core import PacmanState, ACTIONS

class SearchProblem:
    def start_state(self): raise NotImplementedError
    def is_goal(self, state): raise NotImplementedError
    def successors(self, state): raise NotImplementedError  # (next, action, cost)
    def cost_of_actions(self, actions): return len(actions)

@dataclass
class PositionSearchProblem(SearchProblem):
    game: PacmanState
    goal: tuple[int,int]
    start: tuple[int,int] | None = None

    def start_state(self): return self.start or self.game.pacman
    def is_goal(self, state): return state == self.goal
    def successors(self, state):
        out=[]
        for a,(dx,dy) in ACTIONS.items():
            if a == 'Stop': continue
            nxt=(state[0]+dx,state[1]+dy)
            if 0 <= nxt[0] < self.game.width and 0 <= nxt[1] < self.game.height and nxt not in self.game.walls:
                out.append((nxt,a,1))
        return out

@dataclass
class CornersProblem(SearchProblem):
    game: PacmanState
    corners: tuple[tuple[int,int], ...]
    def start_state(self):
        visited=tuple(c for c in self.corners if c == self.game.pacman)
        return (self.game.pacman, frozenset(visited))
    def is_goal(self, state): return len(state[1]) == len(self.corners)
    def successors(self, state):
        pos, visited=state
        out=[]
        for a,(dx,dy) in ACTIONS.items():
            if a == 'Stop': continue
            nxt=(pos[0]+dx,pos[1]+dy)
            if 0 <= nxt[0] < self.game.width and 0 <= nxt[1] < self.game.height and nxt not in self.game.walls:
                nv=set(visited)
                if nxt in self.corners: nv.add(nxt)
                out.append(((nxt, frozenset(nv)), a, 1))
        return out

def null_heuristic(state, problem=None): return 0

def manhattan(a,b): return abs(a[0]-b[0]) + abs(a[1]-b[1])

def corners_heuristic(state, problem: CornersProblem):
    pos, visited=state
    remaining=[c for c in problem.corners if c not in visited]
    h=0; cur=pos
    while remaining:
        d,c=min((manhattan(cur,c),c) for c in remaining)
        h+=d; cur=c; remaining.remove(c)
    return h

def _reconstruct(parent, state):
    actions=[]
    while parent[state][0] is not None:
        state, act = parent[state]
        actions.append(act)
    return list(reversed(actions))

def depth_first_search(problem: SearchProblem):
    start=problem.start_state(); stack=[start]; parent={start:(None,None)}
    while stack:
        s=stack.pop()
        if problem.is_goal(s): return _reconstruct(parent,s)
        for ns,a,c in problem.successors(s):
            if ns not in parent:
                parent[ns]=(s,a); stack.append(ns)
    return []

def breadth_first_search(problem: SearchProblem):
    start=problem.start_state(); q=deque([start]); parent={start:(None,None)}
    while q:
        s=q.popleft()
        if problem.is_goal(s): return _reconstruct(parent,s)
        for ns,a,c in problem.successors(s):
            if ns not in parent:
                parent[ns]=(s,a); q.append(ns)
    return []

def uniform_cost_search(problem: SearchProblem):
    start=problem.start_state(); pq=[(0,0,start)]; parent={start:(None,None)}; dist={start:0}; tick=0
    while pq:
        g,_,s=heapq.heappop(pq)
        if g != dist[s]: continue
        if problem.is_goal(s): return _reconstruct(parent,s)
        for ns,a,c in problem.successors(s):
            ng=g+c
            if ns not in dist or ng < dist[ns]:
                dist[ns]=ng; parent[ns]=(s,a); tick+=1; heapq.heappush(pq,(ng,tick,ns))
    return []

def a_star_search(problem: SearchProblem, heuristic=null_heuristic):
    start=problem.start_state(); pq=[(heuristic(start,problem),0,0,start)]; parent={start:(None,None)}; dist={start:0}; tick=0
    while pq:
        f,g,_,s=heapq.heappop(pq)
        if g != dist[s]: continue
        if problem.is_goal(s): return _reconstruct(parent,s)
        for ns,a,c in problem.successors(s):
            ng=g+c
            if ns not in dist or ng < dist[ns]:
                dist[ns]=ng; parent[ns]=(s,a); tick+=1; heapq.heappush(pq,(ng+heuristic(ns,problem),ng,tick,ns))
    return []
