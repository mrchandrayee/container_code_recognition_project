from dataclasses import dataclass, field
import time

@dataclass
class State:
    hits: int = 0
    misses: int = 0
    locked: bool = False
    confidence: float = 0.0
    box: tuple = (0,0,0,0)
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)

class RecognitionLock:
    """Temporal stabilizer: lock a code after repeated consecutive detections."""
    def __init__(self, lock_after_hits=3, forget_after_misses=18):
        self.lock_after_hits=lock_after_hits
        self.forget_after_misses=forget_after_misses
        self.states={}

    def update(self, reads):
        seen=set()
        now=time.time()
        for r in reads:
            seen.add(r.code)
            s=self.states.setdefault(r.code,State())
            s.hits += 1
            s.misses = 0
            s.confidence = max(s.confidence, r.confidence)
            s.box = r.box
            s.last_seen=now
            if s.hits >= self.lock_after_hits:
                s.locked=True
        for code,s in list(self.states.items()):
            if code not in seen:
                s.misses += 1
                if s.misses > self.forget_after_misses:
                    del self.states[code]
        return self.states

    def snapshot(self):
        return [
            {"container_code":code,"locked":s.locked,"hits":s.hits,
             "confidence":round(s.confidence,3),"first_seen":s.first_seen,
             "last_seen":s.last_seen,"box":s.box}
            for code,s in self.states.items()
        ]
