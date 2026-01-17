from datetime import datetime
import json
import math
import random
import time
import numpy as np
from rnn.simple_rnn import SimpleRNN

class EmotionRegulator:
    """Using a SimpleRNN, calculate PAD deltas using environmental stimuli"""
    def __init__(self, tracked_stimuli: [str], thought_state_size: int, rnn: SimpleRNN=None, ths: np.ndarray=None):
        self.tracked_stimuli = tracked_stimuli
        self.input_size = 3 + len(tracked_stimuli) + 2 # P, A, D, + stimuli, + time of day
        self.rnn = rnn or SimpleRNN(input_size=self.input_size, hidden_size=thought_state_size, output_size=3) 
        self.thought_state = ths if ths is not None else np.zeros(thought_state_size)
        self.input_vec = np.zeros((1, self.input_size))

    @classmethod
    def from_archive(cls, filepath):
        # Load model
        rnn = SimpleRNN.from_archive(filepath + ".rnn.npz")

        # Load saved thought state
        with np.load(filepath + ".ths.npz") as tsf:
            thought_state = tsf["thought_state"]
       
        # Load configured tracked stimuli associated with this model
        with open(filepath + ".ts", "r") as ts:
            tracked_stimuli = json.load(ts)["tracked_stimuli"]

        return cls(tracked_stimuli=tracked_stimuli, thought_state_size=thought_state.shape, rnn=rnn, ths=thought_state)

    def save_to_archive(self, filepath):
        self.rnn.save_to_archive(filepath + ".rnn.npz")
        np.savez(filepath + ".ths.npz", thought_state=self.thought_state)

        with open(filepath + ".ts", "w") as tsf:
            json.dump({"tracked_stimuli": self.tracked_stimuli}, tsf, indent=2)

    def encode_time(self, time: datetime):
        hour = time.hour + time.minute / 60
        angle = hour / 24.0 * 2 * math.pi

        return math.sin(angle), math.cos(angle)

    def next_delta(self, emotion_state, stimuli, time: datetime):
        ivec = self.input_vec[0]
        ivec[0:3] = emotion_state.pad_vector
        hot_indices = [self.tracked_stimuli.index(st) for st in stimuli]
        ivec[3:3+len(self.tracked_stimuli)][hot_indices] = 1.0
        ivec[-2:] = self.encode_time(time)

        pad_delta_series, thought_series = self.rnn.forward(self.input_vec, initial_hidden_state=self.thought_state)
        self.thought_state = thought_series[0]
        pad_delta = pad_delta_series[0]

        return pad_delta


def archive_test():
    er = EmotionRegulator(
            tracked_stimuli = [
                "person",
                "hand",
                "ball",
                "toy"
            ],
            thought_state_size=16
    )

    class MockEmotionState:
        def __init__(self, p, a, d):
            self.pad_vector = np.array([p, a, d])

    es = MockEmotionState(0.50, 0.20, 0.30)

    delta_pad = er.next_delta(es, ["hand", "toy"], datetime.now())
    er.save_to_archive("archive-test")
    delta_pad1 = er.next_delta(es, ["hand", "toy"], datetime.now())

    er2 = EmotionRegulator.from_archive("archive-test")
    es = MockEmotionState(0.50, 0.20, 0.30)
    delta_pad2 = er2.next_delta(es, ["hand", "toy"], datetime.now())


    print(f"Pre-save prediction:\n{delta_pad1}\nPost-load prediction:\n{delta_pad2}")

    assert all(delta_pad1 == delta_pad2), "pre-save and post-load computed deltas do not match"

def forward_apply_test():
    iterations = 5
    er = EmotionRegulator(
            tracked_stimuli = [
                "person",
                "cup",
            ],
            thought_state_size=30
    )

    class MockEmotionState:
        def __init__(self, p, a, d):
            self.pad_vector = np.array([p, a, d])

    es = MockEmotionState(0.50, 0.20, 0.30)

    i = iterations
    while i:
        print(f"PAD: {np.round(es.pad_vector, decimals=3)} ", end="")
        delta_pad = er.next_delta(es, ["person" if random.random() < 0.5 else "cup"], datetime.now())
        print(f"delta: {delta_pad}")
        es.pad_vector += delta_pad
        i -= 1
        time.sleep(1)

if __name__ == "__main__":
    print("===== Archive save/load ======", flush=True)
    archive_test()
    print("\n===== Forward apply test =====",  flush=True)
    forward_apply_test()
