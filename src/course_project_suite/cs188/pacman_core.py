from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Iterable

ACTIONS = {
    "North": (0, -1), "South": (0, 1), "East": (1, 0), "West": (-1, 0), "Stop": (0, 0)
}

@dataclass(frozen=True)
class PacmanState:
    width: int
    height: int
    walls: frozenset[tuple[int,int]]
    pacman: tuple[int,int]
    ghosts: tuple[tuple[int,int], ...]
    food: frozenset[tuple[int,int]]
    capsules: frozenset[tuple[int,int]] = frozenset()
    score: float = 0.0
    win: bool = False
    lose: bool = False

    def legal_actions(self, agent_index: int = 0):
        pos = self.pacman if agent_index == 0 else self.ghosts[agent_index-1]
        actions=[]
        for a,(dx,dy) in ACTIONS.items():
            nx,ny=pos[0]+dx,pos[1]+dy
            if 0 <= nx < self.width and 0 <= ny < self.height and (nx,ny) not in self.walls:
                actions.append(a)
        return actions

    def generate_successor(self, agent_index: int, action: str):
        if self.win or self.lose: return self
        dx,dy=ACTIONS[action]
        score=self.score-0.05
        pac=self.pacman
        ghosts=list(self.ghosts)
        food=set(self.food)
        capsules=set(self.capsules)
        if agent_index == 0:
            pac=(pac[0]+dx,pac[1]+dy)
            if pac in food:
                food.remove(pac); score += 10
            if pac in capsules:
                capsules.remove(pac); score += 25
        else:
            idx=agent_index-1
            g=ghosts[idx]
            ghosts[idx]=(g[0]+dx,g[1]+dy)
        lose = pac in set(ghosts)
        win = len(food)==0 and not lose
        return PacmanState(self.width,self.height,self.walls,pac,tuple(ghosts),frozenset(food),frozenset(capsules),score,win,lose)

    def is_win(self): return self.win
    def is_lose(self): return self.lose
    def num_agents(self): return 1 + len(self.ghosts)

    def render(self) -> str:
        rows=[]
        for y in range(self.height):
            row=[]
            for x in range(self.width):
                p=(x,y)
                if p in self.walls: row.append('%')
                elif p == self.pacman: row.append('P')
                elif p in self.ghosts: row.append('G')
                elif p in self.food: row.append('.')
                elif p in self.capsules: row.append('o')
                else: row.append(' ')
            rows.append(''.join(row))
        return '\n'.join(rows)


def parse_layout(lines: list[str]) -> PacmanState:
    h=len(lines); w=max(len(r) for r in lines)
    walls=set(); food=set(); ghosts=[]; capsules=set(); pac=None
    for y,row in enumerate(lines):
        for x,ch in enumerate(row.ljust(w)):
            if ch == '%': walls.add((x,y))
            elif ch == '.': food.add((x,y))
            elif ch == 'o': capsules.add((x,y))
            elif ch == 'P': pac=(x,y)
            elif ch == 'G': ghosts.append((x,y))
    if pac is None: raise ValueError('layout must contain P')
    return PacmanState(w,h,frozenset(walls),pac,tuple(ghosts),frozenset(food),frozenset(capsules))

TINY_LAYOUT = [
    "%%%%%%%",
    "%P . G%",
    "% %%% %",
    "%  .  %",
    "%%%%%%%",
]
