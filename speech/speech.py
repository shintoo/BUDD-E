from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import re
from enum import Enum
from datetime import datetime
from train import train, load

class Modifier(Enum):
    DISTANCE_SHORT = 5
    DISTANCE_LONG = 10
    TURN_CCW = 2
    TURN_CW = 3

def extract_distance_parameters(command):
    modifiers = {}
    # Fuzzy short/long
    short_match = re.search(r"(little|few inches|bit|slightly|some|)", command)
    if short_match:
        modifiers["distance"] = Modifier.DISTANCE_SHORT
    long_match = re.search(r"(far|farther|lot|quite)", command)
    if long_match:
        modifiers["distance"] = Modifier.DISTANCE_LONG

    # Exact distances
    exact_match = re.search(r"(\d+|a|an) (inch|foot|feet|centimeter|meter|step|pace)", command)
    if exact_match:
        match exact_match.group(1):
            case "a" | "an":
                value = 1
            case number:
                value = int(number)

        match exact_match.group(2):
            case "inch":
                modifiers["distance"] = value * 2.54
            case "feet":
                modifiers["distance"] = value * 2.54 * 12
            case "cenimteters":
                modifiers["distance"] = value
            case "meters":
                modifiers["distance"] = value * 100
            case "steps" | "paces":
                modifiers["distance"] = value * 20
            case _:
                modifiers["distance"] = Modifier.DISTANCE_SHORT

    return modifiers

def extract_turn_parameters(command):
    modifiers = {}

    if "left" in command or ("counter" in command and "clock" in command):
        modifiers["direction"] = "CCW"
    elif "right" in command or "clock" in command:
        modifiers["direction"] = "CW"

    # Extract angle modifier
    angle_match = re.search(r"(\d+)", command)
    if angle_match:
        modifiers["angle"] = int(angle_match.group(1))
    elif "all" in command and "around" in command:
        modifiers["angle"] = 360
    elif "around" in command:
        modifiers["angle"] = 180

    return modifiers

def extract_modifiers(command, intent):
    modifiers = {}

    if intent in ["forward", "reverse"]:
        modifiers.update(extract_distance_parameters(command))

    elif intent == "turn":
        modifiers.update(extract_turn_parameters(command))

    return modifiers

if __name__ == "__main__":
    import sys
    model_filepath = "model.pkl" if len(sys.argv) < 2 else sys.argv[1]
    model = load(model_filepath)

    while True:
        command = input("> ")
        if command == "quit":
            break
        intent = model.predict([command])[0]
        probs = [f"{float(p)*100:.2}" for p in model.predict_proba([command])[0]]
        modifiers = extract_modifiers(command, intent)
        labels = [str(c) for c in model.classes_]
        print(f"Intent: {intent}\nModifiers: {modifiers}\n{list(zip(labels, probs))}")
