import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import math
import traceback
from threading import Thread
from random import randint
from typing import Optional

import numpy as np
from PIL import ImageColor
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import uvicorn

import voice
from speech import SpeechProcessor
from face import Face, EMOTION_COLORS
from head import Head
from emotion import Emotion, EmotionState
from wheels import Wheels
from server import server
from battery import Battery
#from camera import Camera

class BUDD_E:
    def __init__(self, color="teal"):
        self.head = Head(servo_pin=23)
        self.face = Face(color=color)
        self.wheels = Wheels(4, 17, 13, 16, 24, 12) # todo get these from a config file? and do same for tft pins?
        self.battery = Battery()
        #self.camera = Camera()
        self.sp = SpeechProcessor("./speech/model.pkl")
        self.threadpoolexecutor = ThreadPoolExecutor(max_workers=5)
        self.emotion = EmotionState()
        self.disposition = np.array([15., 5., 10.])
        self._boredom_time = 10.0
        self.prev_interaction = datetime.now()
        # This is saved external to self.emotion so we can track when it changes (i.e. compare new label to previous)
        self.emotion_label = self.emotion.label()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.chatting = False
        self.running = False

        server.state.robot = self
        config = uvicorn.Config(server, host="0.0.0.0", port=8000)
        self.server = uvicorn.Server(config)

        #logging.getLogger("uvicorn.error").handlers = []
        #logging.getLogger("uvicorn.error").propagate = False

        #logging.getLogger("uvicorn.access").handlers = []
        #logging.getLogger("uvicorn.access").propagate = False

        #logging.getLogger("uvicorn.asgi").handlers = []
        #logging.getLogger("uvicorn.asgi").propagate = True


        # TODO put this somewhere nicer. Neutral is colored "at runtime" at the moment.
        EMOTION_COLORS[self.emotion.label()] = color

    def start(self):
        self.face.start()
        self.say("hello")
        self.running = True

        server_thread = Thread(target=self.server.run)
        server_thread.start()

    def _terminate(self):
        self.threadpoolexecutor.shutdown()
        self.face.stop()
        self.head.cleanup()


    def quit(self):
        self.set_emotion(emotion=Emotion.NEUTRAL)
        self.face.return_to_anchor()
        time.sleep(0.1)
        self.face.nod()
        self.say("bye")
        time.sleep(0.75)
        self.set_emotion(emotion=Emotion.SLEEPY)
        time.sleep(0.75)
        self._terminate()

    def do(self, task):
        self.threadpoolexecutor.submit(task)

    def say(self, word):
        if not word in voice.words:
            print(f"say: invalid word: {word}")
            word = "okay"
        self.do(lambda: voice.say(word))
        intensities = [((tone-1500, dur)) for tone, dur in voice.words[word]]

        slope = (1.5 - 1.1) / (2100 - 750)
        intensity = lambda tone: 1.1 + slope * (tone - 750)
        intensities = [(intensity(tone), duration) for tone, duration in voice.words[word]]

        self.face.vary_intensity(intensities)

    def yes(self):
        self.say("yes")
        self.face.nod()
        self.head.nod()

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
    def express_status(self):
        match self.emotion_label:
            case Emotion.HAPPY:
                self.say("happy")
                self.face.nod()
            case Emotion.RELAXED:
                self.say("relaxed")
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
            case Emotion.SURPRISED:
                self.say("surprised")
            case Emotion.SCARED:
                self.face.shake()

    def attention(self):
        self.say("yes")
        self.face.gaze_off()
        self.face.return_to_anchor()

    def express(self, emotion: Emotion, expression: str=None):
        """Temporarily express an emotion (e.g. reacting during a chat)"""
        saved_emotion = self.emotion.pad_vector
        saved_expression = self.face.expression # usually None
        self.set_emotion(emotion=emotion)
        self.face.expression = expression
        self.express_status()
        time.sleep(1)
        self.set_emotion(emotion_vector=saved_emotion)
        self.face.expression = saved_expression
        self.face.return_to_anchor()

    def chat(self):
        self.face.return_to_anchor()
        return_to_gaze = self.face.gazing.is_set()
        self.face.gaze_off()
        self.chatting = True
        neutral_reactions = [self.face.nod, self.yes]

        try:
            while self.chatting:
                text = input(f"chat{[int(v) for v in self.emotion.pad_vector]}> ")
                if text == "":
                    continue
                if text == "end chat":
                    self.chatting = False
                    break

                # TODO move sentiment_analyzer to SpeechProcessor
                sentiment = self.sentiment_analyzer.polarity_scores(text)
                print(sentiment)

                if sentiment["compound"] < -0.05:
                    if self.emotion_label == Emotion.MAD:
                        self.laugh()
                    else:
                        self.express(Emotion.SAD)
                        self.impart_effect(np.array([0, -1, 0]))
                elif sentiment["compound"] > 0.05:
                    self.express(Emotion.HAPPY)
                    self.impart_effect(np.array([5., 7., 0.]))
                else:
                    neutral_reactions[randint(0, 1)]()
                    self.impart_effect(np.array([5., 5., 0.]))

        except Exception as e:
            print(f"chat error: {e}")
            print(traceback.format_exc())

        if return_to_gaze:
            self.face.gaze_on()

        self.prev_interaction = datetime.now()

    def impart_effect(self, pad_delta: np.ndarray):
        """ Impart an emotional effect on the emotion state, and update the face as needed """
        # Grab current emotion label (to later check if a change happened)
        previous_label = self.emotion_label
        # Update emotion vector
        self.emotion.update(pad_delta)

        # Update face etc
        self.set_emotion(emotion_vector=self.emotion.pad_vector)

        # "Notify" on emotion label change
        if self.emotion_label != previous_label:
            self.face.return_to_anchor()
            self.express_status()

    def set_emotion(self, emotion_vector: Optional[np.ndarray]=None, emotion: Optional[Emotion]=None, force_color=False):
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
        # Update face expression
        self.face.set_emotion(self.emotion_label, force_color=True)
        # Set face color based on emotion (interpolate)
        #self.face.color = self.color_from_emotion()

    def color_from_emotion(self):
        num_to_blend = 3
        # Get [(Emotion.HAPPY, 123.4), ...] i.e. sorted distances to each emotion
        emotion_distances = self.emotion.all_points_by_distance()[:num_to_blend]
        distances = [d[1] for d in emotion_distances]
        # Colors for each emotion sorted by distance
        colors = [EMOTION_COLORS[emotion[0]] for emotion in emotion_distances]
        # Convert colors to r,g,b,a if not already:
        colors = [ImageColor.getrgb(color) if isinstance(color, str) else color for color in colors]
        # Convert distances to weights
        weights = [1 - (d/sum(distances)) for d in distances]
        weights[0] *= 2 # double closest emotion weight
        print(f"{weights=}")

        final_color = [sum(c[i] * w for c, w in zip(colors, weights)) for i in range(len(colors[0]))]

        #return colors[0]
        return tuple(int(v) for v in final_color)

    def process_command(self, command: str):
        if command == "yes":
            self.face.nod()
            self.head.nod()
            return

        if command.split()[0] == "emotion":
            if len(command.split()) == 1:
                print(self.emotion.label())
            label = command.split()[1].upper()
            if label not in Emotion.__members__:
                print(f"no such emotion {label}")
                return

            self.set_emotion(emotion=Emotion[label])
            self.express_status()

        intent, modifiers = self.sp.process(command)

        if intent == "forward":
            self.face.look("down")
            self.wheels.forward()
            time.sleep(1)
            self.wheels.stop()
        if intent == "reverse":
            self.face.look("up")
            self.wheels.backward()
            time.sleep(1)
            self.wheels.stop()
        if intent == "turn" and modifiers.get("direction", "") == "CW":
            self.face.look("right")
            self.wheels.right()
            time.sleep(0.5)
            self.wheels.stop()
        if intent == "turn" and modifiers.get("direction", "") == "CCW":
            self.face.look("left")
            self.wheels.left()
            time.sleep(0.5)
            self.wheels.stop()
        if intent == "conv_status":
            self.express_status()

    def status(self):
        return {
            "emotion": {
                "vector": list(self.emotion.pad_vector),
                "label": self.emotion.label().name,
                "previous": list(self.emotion.previous()),
            },
            "battery": {
                "percentage": self.battery.percentage(),
                "charging": self.battery.is_charging()
            }
        }

    def update(self, delta):
        # Skip EoT during chat
        if self.chatting:
            return

        # Check for commands
        if not server.state.queue.empty():
            cmd = server.state.queue.get_nowait()
            print(f"BUDD_E got command: {cmd}")
            self.process_command(cmd)

        # TODO move this somewhere else,
        # or implement attractors elsewhere...
        #if (datetime.now() - self.prev_interaction).total_seconds() > self._boredom_time:
        #    if self.emotion.pad_vector[2] >= 0:
        #        print("boredom")
        #        self.impart_effect(np.array([-10., -40., 0.]))
        #    else:
        #        print("lonely")
        #        self.impart_effect(np.array([-30.0, -20.0, 0.]))
        #
        #    self.prev_interaction = datetime.now()

        # Gradually return to disposition over time
        distances_to_disposition = np.sqrt(np.square(self.emotion.pad_vector - self.disposition)) * np.sign(self.disposition - self.emotion.pad_vector)
        speeds = np.array([.05, 0.01, .075]) * delta
        effect_over_time = np.sign(distances_to_disposition * speeds)
        effect_over_time[np.abs(distances_to_disposition) < effect_over_time] = 0.

        self.impart_effect(effect_over_time)

        if randint(1, 30) == 5:
            self.express_status()


def main():
    budd_e = BUDD_E()
    budd_e.start()

    def _update_budde_thread():
        prev = datetime.now()

        while budd_e.running:
            now = datetime.now()
            delta = (now - prev).total_seconds()
            prev = now

            budd_e.update(delta)
            time.sleep(1)

    Thread(target=_update_budde_thread).start()

    while True:
        command = input(f"{[int(v) for v in budd_e.emotion.pad_vector]}> ")
        if command == "":
            continue
        if command == "quit":
            break
        if command.split()[0] == "rotate":
            angle = int(command.split()[1])
            budd_e.face.rotation = angle
            continue
        if command == "explore":
            budd_e.explore()
            continue
        if command == "attention":
            budd_e.attention()
            continue
        if command.split()[0] == "emotion":
            if len(command.split()) == 1:
                print(budd_e.emotion.label())
                continue
            label = command.split()[1].upper()
            if label not in Emotion.__members__:
                print(f"no such emotion {label}")
                continue
            budd_e.set_emotion(emotion=Emotion[label])
            budd_e.express_status()
            continue
        if command.split()[0] == "color":
            budd_e.face.color = command.split()[1]
            continue
        if command == "shake":
            budd_e.face.shake()
            self.say("sad")
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
        if command == "laugh":
            budd_e.laugh()
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
            budd_e.express_status()
            continue

        if command == "chat":
            budd_e.chat()
            continue

        intent, modifiers = budd_e.sp.process(command)

        if intent == "forward":
            budd_e.face.look("down")
            budd_e.wheels.forward()
            time.sleep(1)
            budd_e.wheels.stop()
        if intent == "reverse":
            budd_e.face.look("up")
            budd_e.wheels.backward()
            time.sleep(1)
            budd_e.wheels.stop()
        if intent == "turn" and modifiers.get("direction", "") == "CW":
            budd_e.face.look("right")
            budd_e.wheels.right()
            time.sleep(0.5)
            budd_e.wheels.stop()
        if intent == "turn" and modifiers.get("direction", "") == "CCW":
            budd_e.face.look("left")
            budd_e.wheels.left()
            time.sleep(0.5)
            budd_e.wheels.stop()
        if intent == "conv_status":
            budd_e.express_status()

        print(intent, modifiers)

    budd_e.quit()
    time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Got error starting BUDD-E: {e}. Is pigpiod started? ('sudo pigpiod').")
        input(f"[enter to show traceback]> ")
        traceback.print_exc()


