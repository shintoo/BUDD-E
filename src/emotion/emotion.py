import numpy as np
from random import randint
from enum import Enum, auto

class Emotion(Enum):
    MAD = auto()
    SAD = auto()
    CALM = auto()
    BORED = auto()
    TIRED = auto()
    SLEEPY = auto()
    NEUTRAL = auto()
    PLAYFUL = auto()
    EXCITED = auto()
    FEARFUL = auto()
    CURIOUS = auto()
    RELAXED = auto()
    SURPRISED = auto()  
    UNPLEASANT = auto()
    DISAPPOINTED = auto()


class EmotionState:
    def __init__(self, initial_state: np.ndarray = np.array([0, 0, 0])):
        self.pad_vector = initial_state 

        # emotion: [p_bounds, a_bounds, d_bounds]
        self.bounds = {
            Emotion.NEUTRAL:      [(-25, 25),   (-25, 25),   (-25, 25)],
            Emotion.PLAYFUL:      [(0, 100),    (0, 50),     (0, 100)],
            Emotion.EXCITED:      [(0, 100),    (0, 100),    (0, 100)],
            Emotion.CURIOUS:      [(0, 100),    (-100, 0),   (50, 100)],
            Emotion.RELAXED:      [(0, 100),    (-100, 0),   (0, 50)],
            Emotion.MAD:          [(-100, 0),   (50, 100),   (0, 100)],
            Emotion.UNPLEASANT:   [(-100, 0),   (0, 100),    (0, 100)],
            Emotion.SAD:          [(-100, -50), (-100, -50), (-100, -50)],
            Emotion.BORED:        [(-50, 0),    (-50, 0),    (-100, 0)],
            Emotion.TIRED:        [(-100, 0),   (-100, -50), (-100, 0)],
            Emotion.CALM:         [(0, 100),    (-100, 0),   (-100, 0)],
            Emotion.FEARFUL:      [(-100, 0),   (0, 100),    (-100, 0)],
            Emotion.SURPRISED:    [(0, 100),    (0, 100),    (-100, 0)],
            Emotion.DISAPPOINTED: [(-100, 0),   (-100, 0),   (0, 100)],
        }

    def update(self, delta: np.ndarray):
        self.pad_vector += delta
        self.pad_vector[self.pad_vector > 100.0] = 100.0
    
    def label(self):
        p, a, d = self.pad_vector

        for emotion, bounds in self.bounds.items():
            p_bounds = bounds[0]
            a_bounds = bounds[1]
            d_bounds = bounds[2]

            if (p_bounds[0] <= p <= p_bounds[1] and
                a_bounds[0] <= a <= a_bounds[1] and
                d_bounds[0] <= d <= d_bounds[1]):
                return emotion

        return Emotion.NEUTRAL

    def intensity(self):
        # Normalize to percentage (173 is distance from 0,0,0 at 100,100,100)
        return np.sqrt(np.sum(np.square(self.pad_vector))) / 173

if __name__ == "__main__":
    while True:
        text = input("[p, a, d] or 'random'> ")
        if text == "random":
            values = [randint(-100, 100), randint(-100, 100), randint(-100, 100)]
        else:
            values = [int(v) for v in text.split()]

        emotion_state = EmotionState(np.array(values))
        emotion_label = emotion_state.label()
        intensity = emotion_state.intensity()
        p, a, d = emotion_state.pad_vector
        p = int(p)
        a = int(a)
        d = int(d)
        print(f"[{p=} {a=} {d=}] {emotion_label} {intensity*100:.2f}%") 

