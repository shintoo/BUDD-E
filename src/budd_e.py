import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from typing import Optional

from speech import SpeechProcessor
from face import Face
from emotion import Emotion, EmotionState
import voice

class BUDD_E:
    def __init__(self, color="orange"):
        self.face = Face(color=color)
        self.sp = SpeechProcessor("./speech/model.pkl")
        self.threadpoolexecutor = ThreadPoolExecutor(max_workers=5)
        self.emotion = EmotionState()
        # This is saved external to self.emotion so we can track when it changes (i.e. compare new label to previous)
        self.emotion_label = self.emotion.label()

    def start(self):
        self.face.start()
        self.say("hello")

    def _terminate(self):
        self.threadpoolexecutor.shutdown()
        self.face.stop()

    def quit(self):
        self.set_mood("neutral")
        self.face.return_to_anchor()
        time.sleep(0.1)
        self.face.nod()
        self.say("bye")
        self._terminate()

    def do(self, task):
        self.threadpoolexecutor.submit(task)

    def say(self, word):
        if not word in voice.words:
            print(f"say: invalid word: {word}")
            word = "okay"
        self.do(lambda: voice.say(word))

    def yes(self):
        self.say("yes")
        self.do(self.face.nod)

    def no(self):
        self.say("no")
        self.face.shake_no()

    def thank_you(self):
        self.say("thank you")
        self.face.nod()

    def explore(self):
        self.face.gaze_on()

    def status(self):
        match self.face.mood:
            case "happy":
                self.say("happy")
                self.face.nod()
            case "sad":
                self.say("sad")
            case "mad":
                self.say("mad")
                self.face.shake()
            case "bored":
                self.say("bored")
            case "neutral":
                self.say("bored")
            case "sleepy":
                self.say("sleepy")

    def attention(self):
        self.say("yes")
        self.face.gaze_off()
        self.face.return_to_anchor()

    def set_mood(self, mood):
        self.face.set_mood(mood)
        self.face.return_to_anchor()
        self.status()

    def impart_effect(self, pad_delta: np.ndarray):
        self.emotion.update(pad_delta)
        self._update_expression_from_emotion()

    def set_emotion(self, emotion_vector: Optional[np.ndarray]=None, emotion_enum: Optional[Emotion]=None):
        if not (emotion_vector or emotion_enum):
            print("set_emotion: Must pass emotion_vector or emotion_enum")
            return

        self.emotion.pad_vector = emotion_vector
        self._update_expression_from_emotion()

    def _update_expression_from_emotion(self):
        label = self.emotion.label()

        # label unchanged
        if self.emotion_label == label:
            return

        self.emotion_label = label
        intensity = self.emotion.intensity() #TODO unused at the moment

        match label:
            case Emotion.MAD:
                self.set_mood("mad")
            case Emotion.SAD:
                self.set_mood("sad")
            case Emotion.CALM:
                self.set_mood("neutral")
            case Emotion.BORED:
                self.set_mood("bored")
            case Emotion.TIRED | Emotion.SLEEPY:
                self.set_mood("sleepy") 
            case Emotion.NEUTRAL:
                self.set_mood("neutral")
            case Emotion.PLAYFUL | Emotion.EXCITED:
                self.set_mood("happy") 
            case Emotion.FEARFUL:
                self.set_mood("sad") #TODO
            case Emotion.CURIOUS:
                self.set_mood("neutral") #TODO
            case Emotion.RELAXED:
                self.set_mood("neutral") #TODO
            case Emotion.SURPRISED:  
                self.set_mood("neutral") #TODO
            case Emotion.UNPLEASANT:
                self.set_mood("sad") #TODO
            case Emotion.DISAPPOINTED:
                self.set_mood("sad") #TODO

        print(f"Updated emotion to {self.emotion_label}\nUpdated mood to {self.face.mood}")


def main():
    budd_e = BUDD_E()
    budd_e.start()

    while True:
        command = input("> ")
 
        if command == "quit":
            break
        if command == "explore":
            budd_e.explore()
            continue
        if command == "attention":
            budd_e.attention()
            continue
        if command.split()[0] == "mood":  
            budd_e.set_mood(command.split()[1])
            continue
        if command.split()[0] == "color":
            budd_e.face.color = command.split()[1]
            continue
        if command == "shake":
            budd_e.face.shake()
            continue
        if command == "nod":
            budd_e.face.nod()
            continue
        if command == "yes":
            budd_e.yes()
            continue
        if command == "no":
            budd_e.no()
            continue
        if command == "thank you":
            budd_e.thank_you()
            continue
        if command == "sorry":
            budd_e.sorry()
            continue
        if command.split()[0] == "pad":
            print(f"previous PAD: {budd_e.emotion.pad_vector}")
            pad_delta = np.array([int(v) for v in command.split()[1:]])
            budd_e.impart_effect(pad_delta)
            print(f"new PAD:      {budd_e.emotion.pad_vector}")
            continue

        intent, modifiers = budd_e.sp.process(command)

        if intent == "forward":
            budd_e.face.look("down")
        if intent == "reverse":
            budd_e.face.look("up")
        if intent == "turn" and modifiers.get("direction", "") == "CW":
            budd_e.face.look("right")
        if intent == "turn" and modifiers.get("direction", "") == "CCW":
            budd_e.face.look("left")
        if intent == "conv_status":
            budd_e.status()

        print(intent, modifiers)

    budd_e.quit()
    time.sleep(1)

if __name__ == "__main__":
    main()
