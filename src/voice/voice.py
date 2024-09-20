from pysine import sine
import numpy as np
from threading import Thread
from time import sleep
from random import randint
from pprint import pprint as print

BASE_FREQ = 800

def _play_tone(frequency, duration):
    if not frequency:
        sleep(duration)
        return

    sine(frequency+BASE_FREQ, duration)

def say(label):
    random_mod = randint(0, 75)
    for freq, dur in words[label]:
        if not freq:
            sleep(dur)
            continue

        tone = (freq + random_mod, dur) 

        _play_tone(*tone)

def gradual(frequency, target, duration):
    num = 5
    return [(float(f), duration/num) for f in np.linspace(frequency, target, num=num)]

words = {
    "okay": [
        (1540.0, 0.1),
        (1240.0, 0.1),
    ],
    "yes": [
        (1950, 0.05),
        (2050, 0.1),
    ],
    "no": [
        (1850, 0.1),
        (0, 0.15),
        (1700, 0.15),
    ],
    "thank_you": [
        (1640.0, 0.1),
        (1700.0, 0.025),
        (0, 0.1),
        (1540.0, 0.1),
        (1500.0, 0.2),
    ],
    "sorry": [
        (1640.0, 0.05),
        (1700.0, 0.1),
        (1850.0, 0.1),
    ],
    "giggle": [
        (2000.0, 0.05),
        (0, 0.1),
        (2100.0, 0.05),
        (0, 0.1),
        (2100.0, 0.05),
        (0, 0.1),
    ],
    "laugh": [
        (1800.0, 0.05),
        (1750.0, 0.05),
        (0, 0.1),
        (1800.0, 0.05),
        (1750.0, 0.05),
        (0, 0.1),
        (1800.0, 0.05),
        (1750.0, 0.05),
        (0, 0.1),
    ],
    "happy": [
        *gradual(1900.0, 1700.0, 0.125),
        *gradual(1700.0, 2050.0, 0.1),
        (2050.0, 0.1),
    ],
    "sad": [
        *gradual(1500.0, 1150.0, 0.1),
        (0, 0.2),
        *gradual(1500.0, 1150.0, 0.1),
        (0, 0.2),
        *gradual(1500.0, 1100.0, 0.25),
    ],
    "bored": [
        (1700.0, 0.1),
        (0, 0.5),
        (1600.0, 0.1),
        (0, 0.5),
        (1500.0, 0.1),
    ],
    "mad": [
        (1650.0, 0.1),
        (0, 0.2),
        (1720.0, 0.1),
        (0, 0.2),
        *gradual(1900.0, 2100.0, 0.3),
    ],
    "relaxed": [
        (1500.0, 0.2),
        *gradual(1500, 1300.0, 0.1),
        (1300.0, 0.3),
    ],
    "sleepy": [
        *gradual(1000.0, 1150.0, 0.15),
        (0, 0.5),
        *gradual(950.0, 750.0, 0.15),
        (0, 1.5),
        *gradual(1000.0, 1150.0, 0.15),
        (0, 0.5),
        *gradual(950.0, 750.0, 0.15),
    ],
    "bye": [
        (1840.0, 0.1),
        (0, 0.1),
        (1780.0, 0.15),
    ],
    "hello": [
        (1900.0, 0.15),
        (1830.0, 0.15),
    ],
    # "wowow!"
    "surprised": [
        *gradual(1800.0, 2100.0, 0.1),
        *gradual(2100.0, 1800.0, 0.1),
        *gradual(1800.0, 2500.0, 0.1),
        *gradual(2100.0, 1800.0, 0.2)
    ]
}


if __name__ == "__main__":
    print(words)
#    for word in words:
#        print(word)
#        say(word)
#        sleep(1)
