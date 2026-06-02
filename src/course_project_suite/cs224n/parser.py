from __future__ import annotations
class PartialParse:
    def __init__(self,sentence): self.stack=['ROOT']; self.buffer=list(sentence); self.dependencies=[]
    def parse_step(self,transition):
        if transition=='S':
            if not self.buffer: raise ValueError('empty buffer')
            self.stack.append(self.buffer.pop(0))
        elif transition=='LA':
            if len(self.stack)<2: raise ValueError('need stack')
            dep=self.stack.pop(-2); self.dependencies.append((self.stack[-1],dep))
        elif transition=='RA':
            if len(self.stack)<2: raise ValueError('need stack')
            dep=self.stack.pop(); self.dependencies.append((self.stack[-1],dep))
        else: raise ValueError(transition)
    def parse(self,transitions):
        for t in transitions: self.parse_step(t)
        return self.dependencies

def minibatch_parse(sentences,model,batch_size=4):
    partial=[PartialParse(s) for s in sentences]; unfinished=partial[:]
    while unfinished:
        batch=unfinished[:batch_size]; transitions=model.predict(batch)
        for pp,t in zip(batch,transitions):
            pp.parse_step(t)
        unfinished=[p for p in unfinished if not (len(p.buffer)==0 and len(p.stack)==1)]
    return [p.dependencies for p in partial]
