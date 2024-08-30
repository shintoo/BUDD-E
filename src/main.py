import time

from speech import SpeechProcessor
from face import Face
import voice

def main():
    face = Face(color="orange")
    sp = SpeechProcessor("./speech/model.pkl")

    face.start()
    voice.hello()

    while True:
        command = input("> ")
 
        if command == "quit":
            break
        if command == "gaze":
            face.gaze_on()
            continue
        if command == "nod":
            face.nod()
            continue
        if command == "attention":
            voice.say(voice.okay)
            face.return_to_anchor()
            face.gaze_off()
            continue
        if command.split()[0] == "mood": 
            face.set_mood(command.split()[1]) 
            match face.mood:
                case "happy":
                    voice.say(voice.happy)
                case "sad":
                    voice.say(voice.sad)
                case "mad":
                    voice.say(voice.mad)
                case "bored":
                    voice.say(voice.bored)
                case "neutral":
                    voice.say(voice.happy)
                case "sleepy":
                    voice.say(voice.sleepy)
            continue

        if command.split()[0] == "color":
            face.color = command.split()[1]
            continue

        intent, modifiers = sp.process(command)

        if intent == "forward":
            face.look("down")
        if intent == "reverse":
            face.look("up")
        if intent == "turn" and modifiers.get("direction", "") == "CW":
            face.look("right")
        if intent == "turn" and modifiers.get("direction", "") == "CCW":
            face.look("left")
        if intent == "conv_status":
            match face.mood:
                case "happy":
                    voice.say(voice.happy)
                case "sad":
                    voice.say(voice.sad)
                case "mad":
                    voice.say(voice.mad)
                case "bored":
                    voice.say(voice.bored)
                case "neutral":
                    voice.say(voice.happy)
                case "sleepy":
                    voice.say(voice.sleepy)

        print(intent, modifiers)

    face.mood = "neutral"
    face.color = "orange"
    voice.bye()
    face.return_to_anchor()
    time.sleep(1)
    face.stop()

if __name__ == "__main__":
    main()
