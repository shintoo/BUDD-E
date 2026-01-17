import numpy as np
from random import randint
from enum import Enum, auto


class Emotion(Enum):
    NEUTRAL = (0., 0., 0.,)
    HAPPY = (0.6, 0.2, 0.2)
    EXCITED = (0.8, 0.9, 0.5)
    RELAXED = (0.5, -0.4, 0.3)
    SAD = (-0.6, -0.4, -0.5)
    ANXIOUS = (-0.3, 0.6, -0.6)
    MAD = (-0.7, 0.7, 0.7)
    SCARED = (-0.8, 0.8, 0.8)
    BORED = (-0.2, -0.5, -0.2)
    SLEEPY = (0.1, -0.8, 0.1)
    TIRED = (-0.3, -0.7, -0.4)
    SURPRISED = (0.2, 0.8, -0.2)

class EmotionState:
    def __init__(self, initial_state: np.ndarray = np.array([0., 0., 0.])):
        self.pad_vector = initial_state.copy()
        self._previous = initial_state.copy()

    def update(self, delta: np.ndarray): 
        self._previous = self.pad_vector.copy()
        self.pad_vector += delta
        self.pad_vector[self.pad_vector > 1.0] = 1.0
        self.pad_vector[self.pad_vector < -1.0] = -1.0
  
    def set_from_label(self, emotion: Emotion):
        self._previous = self.pad_vector.copy()
        self.pad_vector = np.array(emotion.value)

    def all_points_by_distance(self):
        def distance(p1, p2):
            return np.sqrt((p1[0] - p2[0]) ** 2 +
                (p1[1] - p2[1]) ** 2 +
                (p1[2] - p2[2]) ** 2 )

        distances = [(emotion, distance(self.pad_vector, emotion.value)) for emotion in Emotion]
        distances.sort(key=lambda result: result[1])

        return distances

    def label(self):
        return self.all_points_by_distance()[0][0]

    def intensity(self):
        # Normalize to percentage (1.73 is distance from 0,0,0 at 1.0,1.0,1.0)
        return np.sqrt(np.sum(np.square(self.pad_vector))) / 1.73

    def previous(self):
        return self._previous

    @property
    def P(self):
        return self.pad_vector[0]

    @property
    def A(self):
        return self.pad_vector[1]

    @property
    def D(self):
        return self.pad_vector[2]


if __name__ == "__main__":
    es = EmotionState()

    while True:
        text = input("<p> <a> <d> or 'random' or 'delta p a d'> ")
        if text == "random":
            values = [randint(-1.0, 1.0), randint(-1.0, 1.0), randint(-1.0, 1.0)]
        elif text.split()[0] == 'delta':
            es.update(np.array([float(v) for v in text.split()[1:]]))
        else:
            es.pad_vector = np.array([float(v) for v in text.split()])

        emotion_label = es.label()
        intensity = es.intensity()
        p, a, d = es.pad_vector
        p = float(p)
        a = float(a)
        d = float(d)
        print(f"[{p=} {a=} {d=}] {emotion_label} {intensity*1.0:.2f}%")
