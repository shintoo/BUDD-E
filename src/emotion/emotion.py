import numpy as np
from random import randint
from enum import Enum, auto

class Emotion(Enum):
    HAPPY = (55, 24, 28)
    EXCITED = (55, 70, 70)
    SAD = (-18, -3, -14)
    ANXIOUS = (-20, 50, -50)
    MAD = (-40, 22, 12)
    SLEEPY = (0, -80, -30)
    TIRED = (-30, -70, -50)
    RELAXED = (20, -50, 30)
    NEUTRAL = (0, 0, 0)
    SCARED = (-19, 26, -13)
    SURPRISED = (34, 34, 4)
    BORED = (-20, -50, -30)

class EmotionState:
    def __init__(self, initial_state: np.ndarray = np.array([0, 0, 0])):
        self.pad_vector = initial_state

    def update(self, delta: np.ndarray):
        self.pad_vector += delta
        self.pad_vector[self.pad_vector > 100.0] = 100.0
        self.pad_vector[self.pad_vector < -100.0] = -100.0
  
    def set_from_label(self, emotion: Emotion):
        self.pad_vector = np.array(emotion.value)

    def label(self):
        def distance(p1, p2):
            return np.sqrt((p1[0] - p2[0]) ** 2 +
                (p1[1] - p2[1]) ** 2 +
                (p1[2] - p2[2]) ** 2 )

        distances = [(emotion, distance(self.pad_vector, emotion.value)) for emotion in Emotion]
        distances.sort(key=lambda result: result[1])

        return distances[0][0]

    def intensity(self):
        # Normalize to percentage (173 is distance from 0,0,0 at 100,100,100)
        return np.sqrt(np.sum(np.square(self.pad_vector))) / 173

if __name__ == "__main__":
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
