"""Pure timing and input history; no display or hardware dependencies."""
from collections import deque
import math

class Timeline:
    def __init__(self, capacity=20000):
        self.events = deque(maxlen=capacity)
        self.active = {}
        self.sequence = 0

    def update(self, device, controls, elapsed):
        previous = self.active.get(device, set())
        for control in sorted(previous ^ controls):
            self.sequence += 1
            self.events.append(dict(seq=self.sequence, device=device, control=control,
                                    down=control in controls, time=elapsed))
        self.active[device] = set(controls)

    def remove(self, device, elapsed):
        self.update(device, set(), elapsed)
        self.active.pop(device, None)

    @staticmethod
    def frame(elapsed, fps):
        if not math.isfinite(fps) or fps <= 0:
            raise ValueError('FPS must be positive and finite')
        return math.floor(elapsed * fps)

    def snapshot(self, elapsed, devices):
        return dict(time=elapsed, devices=devices, sequence=self.sequence,
                    active={str(k): sorted(v) for k, v in self.active.items()},
                    events=list(self.events))
