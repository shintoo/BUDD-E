import numpy as np
from random import randint
from enum import Enum, auto

class Emotion(Enum):
    HAPPY = (55.0, 24.0, 28.0)
    EXCITED = (55.0, 70.0, 70.0)
    SAD = (-18.0, -3.0, -14.0)
    ANXIOUS = (-20.0, 50.0, -50.0)
    MAD = (-40.0, 22.0, 12.0)
    SLEEPY = (0.0, -80.0, -30.0)
    TIRED = (-30.0, -70.0, -50.0)
    RELAXED = (20.0, -50.0, 50.0)
    NEUTRAL = (0.0, 0.0, 0.0)
    SCARED = (-19.0, 26.0, -13.0)
    SURPRISED = (34.0, 34.0, 4.0)
    BORED = (-20.0, -50.0, 20.0)

class EmotionState:
    def __init__(self, initial_state: np.ndarray = np.array([0., 0., 0.])):
        self.pad_vector = initial_state.copy()
        self._previous = initial_state.copy()

    def update(self, delta: np.ndarray): 
        self._previous = self.pad_vector.copy()
        self.pad_vector += delta
        self.pad_vector[self.pad_vector > 100.0] = 100.0
        self.pad_vector[self.pad_vector < -100.0] = -100.0
  
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
        # Normalize to percentage (173 is distance from 0,0,0 at 100,100,100)
        return np.sqrt(np.sum(np.square(self.pad_vector))) / 173

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


if __name__ = "__main__":
    es = EmotionState()

    while True:
        text = input("<p> <a> <d> or 'random' or 'delta p a d'> ")
        if text == "random":
            values = [randint(-100, 100), randint(-100, 100), randint(-100, 100)]
        elif text.split()[0] == 'delta':
            es.update(np.array([int(v) for v in text.split()[1:]]))
        else:
            es.pad_vector = np.array([int(v) for v in text.split()])

        emotion_label = es.label()
        intensity = es.intensity()
        p, a, d = es.pad_vector
        p = int(p)
        a = int(a)
        d = int(d)
        print(f"[{p=} {a=} {d=}] {emotion_label} {intensity*100:.2f}%")
