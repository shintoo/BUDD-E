import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import traceback
from random import randint
from typing import Optional

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

import voice
from speech import SpeechProcessor
from face import Face
from emotion import Emotion, EmotionState


class BUDD_E:
    def __init__(self, color="teal"):
        self.face = Face(color=color)
        self.sp = SpeechProcessor("./speech/model.pkl")
        self.threadpoolexecutor = ThreadPoolExecutor(max_workers=5)
        self.emotion = EmotionState()
        self.face.pad_vector = self.emotion.pad_vector
        # This is saved external to self.emotion so we can track when it changes (i.e. compare new label to previous)
        self.emotion_label = self.emotion.label()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.chatting = True

    def start(self):
        self.face.start()
        self.say("hello")

    def _terminate(self):
        self.threadpoolexecutor.shutdown()
        self.face.stop()

    def quit(self):
        self.set_emotion(emotion=Emotion.NEUTRAL)
        self.face.return_to_anchor()
        time.sleep(0.1)
        self.face.nod()
        self.say("bye")
        time.sleep(0.75)
        self.set_emotion(emotion=Emotion.SLEEPY)
        self._terminate()

    def do(self, task):
        self.threadpoolexecutor.submit(task)

    def say(self, word):
        if not word in voice.words:
            print(f"say: invalid word: {word}")
            word = "okay"
        print(f"saying {word}")
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

    def laugh(self):
        self.say("laugh")
        self.face.laugh()

    def explore(self):
        self.face.gaze_on()

    # TODO update to match self.emotion
    def status(self):
        match self.emotion_label:
            case Emotion.HAPPY:
                self.say("happy")
                self.face.nod()
            case Emotion.SAD:
                self.say("sad")
            case Emotion.MAD:
                self.say("mad")
                self.face.shake()
            case Emotion.BORED:
                self.say("bored")
            case Emotion.NEUTRAL:
                self.say("happy")
            case Emotion.SLEEPY:
                self.say("sleepy")

    def attention(self):
        self.say("yes")
        self.face.gaze_off()
        self.face.return_to_anchor()

    def actively_listen(self):
        print("now actively listening")
        self.actively_listening = True
        actions = [self.face.nod, self.yes, lambda: self.say("okay")] # TODO others

        def _active_listening_loop():
            try:
                while self.actively_listening: 
                    time.sleep(randint(1, 8))
                    actions[randint(0, len(actions)-1)]()
                    self.face.return_to_anchor()
            except Exception as e:
                print(e)

        self.do(_active_listening_loop)

    def express(self, emotion: Emotion, expression: str=None):
        """Temporarily express an emotion (e.g. reacting during a chat)"""
        saved_emotion = self.emotion.pad_vector
        saved_expression = self.face.expression # usually None
        self.set_emotion(emotion=emotion)
        self.face.expression = expression
        self.status()
        time.sleep(1)
        self.set_emotion(emotion_vector=saved_emotion)
        self.face.expression = saved_expression
        self.face.return_to_anchor()

    def chat(self):
        self.face.return_to_anchor()
        self.face.gaze_off()
        self.chatting = True
        neutral_reactions = [self.face.nod, self.yes] 
        try:
            while self.chatting:
                text = input("chat> ")

                if text == "end chat":
                    self.chatting = False
                    break

                sentiment = self.sentiment_analyzer.polarity_scores(text)
                print(sentiment)

                if sentiment["compound"] < -0.05:
                    if self.emotion_label == Emotion.MAD:
                        self.laugh()
                    else:
                        self.express(Emotion.SAD) 
                elif sentiment["compound"] > 0.05:
                    self.express(Emotion.HAPPY)
                    self.impart_effect(np.array([10, 7, 0]))
                else:
                    neutral_reactions[randint(0, 1)]()
                    self.impart_effect(np.array([5, 5, 0]))

        except Exception as e:
            print(f"chat error: {e}")
            print(traceback.format_exc())

        self.face.gaze_on()

    def impart_effect(self, pad_delta: np.ndarray):
        """ Impart an emotional effect on the emotion state, and update the face as needed """
        # Grab current emotion label (to later check if a change happened)
        previous_label = self.emotion_label
        # Update emotion vector
        self.emotion.update(pad_delta)
        # Update stored label
        self.emotion_label = self.emotion.label()
        # Update face
        self.face.set_emotion(emotion=self.emotion_label)

        # "Notify" on emotion label change
        if self.emotion_label != previous_label:
            self.face.return_to_anchor()
            #self.status()

    def set_emotion(self, emotion_vector: Optional[np.ndarray]=None, emotion: Optional[Emotion]=None):
        """ Set the emotion via a vector or label, and update the face as needed """
        # Grab current emotion label (to later check if a change happened)
        previous_label = self.emotion_label

        # Update emotion vector, by label, or by overwriting vector
        if emotion:
            self.emotion.set_from_label(emotion)
        elif emotion_vector is not None:
            self.emotion.pad_vector = emotion_vector
        else:
            print("set_emotion: Must pass emotion_vector or emotion_enum")
            return

        # Update stored current label
        self.emotion_label = self.emotion.label()
        # Update face
        self.face.set_emotion(self.emotion_label)

        # "Notify" on emotion label change
        # TODO this should happen outside of this function, because this is used in other ways
        if self.emotion_label != previous_label:
            self.face.return_to_anchor()
            #self.status()

def main():
    budd_e = BUDD_E()
    budd_e.start() 

    while True:
        print(f"{[int(v) for v in budd_e.emotion.pad_vector]}")
        command = input("> ")

        if command == "quit":
            break
        if command == "explore":
            budd_e.explore()
            continue
        if command == "attention":
            budd_e.attention()
            continue
        if command.split()[0] == "emotion":
            label = command.split()[1]
            if label not in Emotion.__members__:
                print(f"no such emotion {label}")
                continue
            budd_e.set_emotion(emotion=Emotion[label])
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
        if command == "status":
            budd_e.status()
            continue

        if command == "chat":
            budd_e.chat()
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
