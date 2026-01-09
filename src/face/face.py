import math
import os
import sys
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import random
from datetime import datetime
import numpy as np

import spidev as SPI
import colorsys
from PIL import Image,ImageDraw,ImageFont,ImageColor,ImageOps,ImageEnhance

from .gc9a01 import GC9A01
from emotion import Emotion

DELTA_TIME_CONSTANT = 18.0

EMOTION_COLORS = {
    Emotion.HAPPY: "yellow",
    Emotion.EXCITED: "chartreuse",
    Emotion.SAD: "blue",
    Emotion.ANXIOUS: "orange",
    Emotion.MAD: "red",
    Emotion.SLEEPY: "purple",
    Emotion.TIRED: "slateblue",
    Emotion.RELAXED: "green",
    Emotion.BORED: "gray",
    Emotion.SCARED: "orangered",
    Emotion.SURPRISED: "gold",
}

def rounded_rectangle(self: ImageDraw, xy, corner_radius=0, fill=None, outline=None):
    upper_left_point = xy[0]
    bottom_right_point = xy[1]
    self.rectangle(
        [
            (upper_left_point[0], upper_left_point[1] + corner_radius),
            (bottom_right_point[0], bottom_right_point[1] - corner_radius)
        ],
        fill=fill,
        outline=outline
    )
    self.rectangle(
        [
            (upper_left_point[0] + corner_radius, upper_left_point[1]),
            (bottom_right_point[0] - corner_radius, bottom_right_point[1])
        ],
        fill=fill,
        outline=outline
    )
    self.pieslice([upper_left_point, (upper_left_point[0] + corner_radius * 2, upper_left_point[1] + corner_radius * 2)],
        180,
        270,
        fill=fill,
        outline=outline
    )
    self.pieslice([(bottom_right_point[0] - corner_radius * 2, bottom_right_point[1] - corner_radius * 2), bottom_right_point],
        0,
        90,
        fill=fill,
        outline=outline
    )
    self.pieslice([(upper_left_point[0], bottom_right_point[1] - corner_radius * 2), (upper_left_point[0] + corner_radius * 2, bottom_right_point[1])],
        90,
        180,
        fill=fill,
        outline=outline
    )
    self.pieslice([(bottom_right_point[0] - corner_radius * 2, upper_left_point[1]), (bottom_right_point[0], upper_left_point[1] + corner_radius * 2)],
        270,
        360,
        fill=fill,
        outline=outline
    )


ImageDraw.rounded_rectangle = rounded_rectangle

class Face(threading.Thread):
    def __init__(self, emotion=Emotion.NEUTRAL, eye_width=40, eye_height=60, distance=60, radius=12, color="lightseagreen", anchor=[120, 120]):
        super().__init__()
        self.emotion = emotion
        self.expression = None
        self.eye_width = eye_width
        self.eye_height = eye_height
        self.distance = distance
        self.radius = radius
        self.color = color
        self.display = GC9A01(spi=SPI.SpiDev(0, 0),spi_freq=80000000,rst=27,dc=25,bl=18)
        self.display.Init()
        self.display.clear()
        self.display.bl_DutyCycle(50)
        self.image = Image.new("RGBA", (self.display.width, self.display.height), "black")
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.truetype("assets/font.otf", 72)
        self.anchor = anchor
        self.position = [self.anchor[0], self.anchor[1]]
        self.velocity = [0, 0]
        self.blinking = False
        self.gazing = threading.Event()
        self.target = None
        self.scaling = False
        self.background = Image.open("assets/bg.png").convert("L")
        self.intensity = 1.0
        self._blink_opening = False
        self._blink_closing = False
        self.rotation = 0
        self.defaults = {
            "eye_height": eye_height,
            "eye_width": eye_width,
            "distance": distance,
            "emotion": emotion,
            "radius": radius,
            "color": color,
        }

        self.LOWER_BOUND_X = 80
        self.UPPER_BOUND_X = 160
        self.LOWER_BOUND_Y = 80
        self.UPPER_BOUND_Y = 160

        self.threadpoolexecutor = ThreadPoolExecutor(max_workers=5)

    def clear(self):
        self.draw.rectangle((0, 0, self.display.width, self.display.height), fill="black")

    def render(self):
        self.clear()
        self._draw_eyes()
        self._draw_mouth()
        self._draw_extras() 

        # Make black areas of face transparent
        data = np.array(self.image)
        r, g, b, a = data.T
        black_areas = (r == 0) & (g == 0) & (b == 0) & (a == 255)
        data[...][black_areas.T] = (0, 0, 0, 0)

        # Draw background and then face on top
        face = Image.fromarray(data)
        self._draw_background()
        self.image.paste(face, (0, 0), face)
        if self.rotation:
            self.display.ShowImage(self.image.rotate(self.rotation))
        else:
            self.display.ShowImage(self.image)

    def set_color(self, color):
        """Color can be a CSS color string or (r, g, b, a)"""
        self.color = color

    def _draw_extras(self):
        match self.emotion:
            case Emotion.SLEEPY:
                self.draw.text((120, 40), "z", fill=self.color, font=self.font)
                self.draw.text((160, 35), "Z", fill=self.color, font=self.font)

    def _draw_mouth(self):
        x, y = self.position
        # xy is center between eyes
        top = self.defaults["eye_height"] / 2 + y
        left = x - 15
        right = x + 15
        bottom = top + 20

        match [self.emotion, self.expression]:
            case Emotion.BORED | Emotion.TIRED, _:
                self.draw.line(((left, top+10), (right, top+10)), fill=self.color, width=6)
            case Emotion.MAD | Emotion.SAD | Emotion.ANXIOUS, _:
                self.draw.arc(((left, top), (right, bottom)), start=180, end=0, fill=self.color, width=6)
            case Emotion.SLEEPY | Emotion.SCARED, _:
                self.draw.circle((x, top), radius=6, fill=self.color)
            case Emotion.SURPRISED, _:
                self.draw.circle((x, top+5), radius=10, fill=self.color)
            case Emotion.EXCITED, _:
                self.draw.arc(((left+3, top), (right-3, bottom+10)), start=0, end=180, fill=self.color, width=6)
                self.draw.arc(((left+3, top+8), (right-3, top+20)), start=180, end=360, fill=self.color, width=6)
                self.draw.circle((left+(right-left)/2, top+(bottom-top+10)/2+4), radius=9, fill=self.color)
                #self.draw.line(((left, top+12), (right, top+12)), fill=self.color, width=6)
            case _, "laughing":
                self.draw.arc(((left, top), (right, bottom)), start=0, end=180, fill=self.color, width=6)
                self.draw.line(((left, top+12), (right, top+12)), fill=self.color, width=6)
            case _:
                self.draw.arc(((left, top), (right, bottom)), start=0, end=180, fill=self.color, width=6)

    def _draw_eye(self, x, y, scale=1, side="left"):
        # xy is center of eye, but rounded_rectangle takes top left and bottom right corners
        hw = self.eye_width / 2
        hh = self.eye_height / 2

        if self.emotion == Emotion.SURPRISED:
            scale = 1.333

        extra_height = (hh * scale) - hh

        x1 = x - hw
        x2 = x + hw
        y1 = y - hh - extra_height
        y2 = y + hh


        self.draw.rounded_rectangle(((x1, y1), (x2, y2)), self.radius, fill=self.color)

        match self.emotion:
            case Emotion.HAPPY:
                self.draw.circle((x, y2+110), 120, fill="black")
            case Emotion.EXCITED:
                self.draw.circle((x, y2+50), 70, fill="black")
            case Emotion.MAD:
                self.draw.circle((x+10 if side == "left" else x-10, y1-20), 50, fill="black")
            case Emotion.SAD:
                self.draw.circle((x-10 if side == "left" else x+10, y1-50), 70, fill="black")
            case Emotion.SCARED:
                self.draw.circle((x-10 if side == "left" else x+10, y1-20), 50, fill="black")
            case Emotion.BORED:
                self.draw.rectangle(((x1, y1-10), (x2, y1+10)), fill="black")
            case Emotion.SLEEPY:
                self.draw.circle((x, y1-20), 70, fill="black")
            case Emotion.TIRED:
                self.draw.circle((x, y1-35), 70, fill="black")
            case Emotion.ANXIOUS:
                self.draw.circle((x-15 if side == "left" else x+15, y1-60), 70, fill="black")
                self.draw.circle((x, y2+60), 70, fill="black")
        match self.expression:
            case "no":
                self.draw.rectangle(((x1, y1-10), (x2, y1+5)), fill="black")
            case "laughing":
                self.draw.circle((x, y2+50), 70, fill="black")

    def _draw_eyes(self):
        # xy is center of face
        x, y = self.position

        y += 10

        hd = self.distance / 2 + self.eye_width / 2
        scale_left = 1
        scale_right = 1

        # Scale eye sizes for looking to the left and right, e.g. ( o O) and (O o )
        if self.scaling:
            if x < self.display.width / 2:
                dist_from_center = self.display.width / 2 - x
                normalized_dist = dist_from_center / (self.display.width/2 - self.LOWER_BOUND_X)
                scale_left = min(1.0 + (normalized_dist / 2)**2, 1.45)
                scale_right = 1.0 - (normalized_dist / 2)**2
            elif x > self.display.width / 2:
                dist_from_center = x - self.display.width / 2
                normalized_dist = dist_from_center / (self.UPPER_BOUND_X - self.display.width/2)
                scale_right = min(1.0 + (normalized_dist / 2)**2, 1.45)
                scale_left = 1.0 - (normalized_dist / 2)**2

            hd = self.distance * (1.5 * min(scale_left, scale_right)) / 2 + self.eye_width / 2
        e1_x = x - hd
        e2_x = x + hd

        self._draw_eye(e1_x, y, scale_left, side="left")
        self._draw_eye(e2_x, y, scale_right, side="right")

    def move(self, x, y):
        self.position = (self.position[0] + x, self.position[1] + y)

    def place(self, x, y):
        self.position = [x, y]

    def move_to_relative(self, xdelta, ydelta, speed=7.0):
        self.move_to(self.position[0]+xdelta, self.position[1]+ydelta, speed=speed)

    def move_to(self, x, y, speed=7.0):
        x1, y1 = self.position
        delta_pos = [x - x1, y - y1]

        if delta_pos == [0, 0]:
            return

        distance = math.sqrt(delta_pos[0]**2 + delta_pos[1]**2)
        time = distance / speed
        self.velocity = [(x - x1) / time, (y - y1) / time]
        self.target = [x, y]

    def nod(self):
        def _nod():
            origin = tuple(self.position)
            self.move_to_relative(0, 20)
            while self.target:
                time.sleep(0.1)
            self.move_to(*origin, speed=3)
        self._submit(_nod)

    def _submit(self, task):
        self.threadpoolexecutor.submit(task)

    def shake_no(self):
        def _shake_no():
            self.expression = "no"
            origin = tuple(self.position)

            self.move_to(origin[0], origin[1]+5)
            self.move_to(origin[0]-10, origin[1])
            while self.target:
                time.sleep(0.05)
            time.sleep(0.15)
            self.move_to(origin[0]+10, origin[1])
            while self.target:
                time.sleep(0.05)
            time.sleep(0.15)
            self.move_to(origin[0]-15, origin[1])
            while self.target:
                time.sleep(0.05)
            self.expression = "neutral"
            self.return_to_anchor()

        self._submit(_shake_no)

    def shake(self):
        def _shake():
            origin = tuple(self.position)
            xdeltas = [-8, 8, -15, 15, -15, 15, -15]
            speeds = [5, 5, 10, 10, 10, 10, 10]
            delays = [0.2, 0.2, 0.01, 0.01, 0.01, 0.01, 0.01]

            for x, d, s in zip(xdeltas, delays, speeds):
                self.move_to(origin[0]+x, origin[1], speed=s)
                while self.target:
                    time.sleep(d)

            time.sleep(0.15)
            self.return_to_anchor()

        self._submit(_shake)

    def laugh(self):
        def _laugh():
            try:
                self.expression = "laughing"
                origin = tuple(self.position)
                ydeltas = [-15, 0, -15, 0, -15]
                speeds = [5, 5, 5, 5, 5]
                delays = [0.08]*5

                for y, d, s in zip(ydeltas, delays, speeds):
                    self.move_to(origin[0], origin[1]+y, speed=s)
                    while self.target:
                        time.sleep(d)

                time.sleep(0.15)
                self.expression = None
                self.return_to_anchor()
            except Exception as e:
                print(e)

        self._submit(_laugh)

    def return_to_anchor(self, speed=7):
        self.move_to(self.anchor[0], self.anchor[1], speed)

    def out_of_bounds(self, safe=False):
        margin = 0 if not safe else 60
        if self.position[0] + self.eye_width + self.distance / 2 >= self.display.width - margin:
            return True
        if self.position[0] - self.eye_width - self.distance / 2 <= margin:
            return True
        if self.position[1] + self.eye_height / 2  >= self.display.height - margin:
            return True
        if self.position[1] - self.eye_height / 2 <= margin:
            return True

    def random_within_bounds(self):
        return [random.randint(self.LOWER_BOUND_X, self.UPPER_BOUND_X), random.randint(self.LOWER_BOUND_Y, self.UPPER_BOUND_Y)]



    def set_emotion(self, emotion: str, force_color=False):
        self.emotion = emotion

        if not force_color:
           return

        if emotion == Emotion.NEUTRAL:
            self.color = self.defaults["color"]
        else:
            self.color = EMOTION_COLORS[self.emotion]
 
    def blink(self):
        if self.blinking:
            return

        self.blinking = True
        self._blink_closing = True

    def look(self, direction, speed=7):
        match direction:
            case "left":
                self.move_to(self.LOWER_BOUND_X, self.anchor[1], speed=speed)
            case "right":
                self.move_to(self.UPPER_BOUND_X, self.anchor[1], speed=speed)
            case "up":
                self.move_to(self.anchor[0], self.LOWER_BOUND_Y, speed=speed)
            case "down":
                self.move_to(self.anchor[0], self.UPPER_BOUND_Y, speed=speed)
            case "center":
                self.return_to_anchor()

    def gaze_on(self, on=True):
        self.gazing.set()

        def _gaze_on():
            while self.gazing.is_set():
                self.move_to(*self.random_within_bounds(), speed=random.randint(5, 10))
                time.sleep(random.randint(3, 8))

        self._submit(_gaze_on)

    def gaze_off(self):
        self.gazing.clear()

    def update(self, delta):
        if random.randint(1, 120) == 2:
            self.blink()
        if self.blinking:
            self._update_blink(delta)
        if self.target:
            self._update_move_to(delta)
        self._update_position(delta)

    def _update_position(self, delta):
        self.position[0] += self.velocity[0] * delta
        self.position[1] += self.velocity[1] * delta

    def _update_move_to(self, delta):
        speed = math.sqrt(self.velocity[0]**2 + self.velocity[1]**2)
        margin = int(speed)

        if not self.target:
            return
        if (self.position[0] >= self.target[0] - margin and self.position[0] <= self.target[0] + margin
           and self.position[1] >= self.target[1] - margin and self.position[1] <= self.target[1] + margin):
            self.velocity = [0, 0]
            self.target = None

    def _update_blink(self, delta):
        if not self.blinking:
            return
        if self._blink_closing:
            self.eye_height -= 20 * delta
            if self.eye_height <= 0:
                self._blink_closing = False
                self._blink_opening = True
        if self._blink_opening:
            self.eye_height += 20 * delta
            if self.eye_height >= self.defaults["eye_height"]:
                self.eye_height = self.defaults["eye_height"]
                self.blinking = False
                self._blink_opening = False

    def stop(self):
        self.running = False
        self.threadpoolexecutor.shutdown()

    def run(self):
        self.running = True
        prev = datetime.now()

        while self.running:
            now = datetime.now()
            delta = (now - prev).total_seconds() * DELTA_TIME_CONSTANT

            self.update(delta)
            self.render()

            prev = now

    def _draw_background(self):
        bg = ImageOps.colorize(self.background, black="black", mid=self.color, white=self.color)  
        enhancer = ImageEnhance.Brightness(bg)
        bg = enhancer.enhance(self.intensity)
        self.image.paste(bg, (0, 0)) 

    def vary_intensity(self, intensities):
        """intensities is a lits of 2 int tuples, where the first is a brightness factor, and the second is a duration"""
        def _vary():
            try:
                for intensity, duration in intensities:
                    if intensity == 0:
                        self.intensity = 1.05
                    else:
                        # scale intensity to pitch etc
                        self.intensity = intensity

                        # Random positive intensity
                        #self.intensity = random.uniform(1.1, 1.5)

                    time.sleep(duration)
            except:
                print(traceback.format_exc())
            self.intensity = 1.0

        self._submit(_vary)

        
if __name__ == "__main__":
    face = Face(color="seagreen", eye_height=40, eye_width=40)
    face.start()

    while True:
        width, height, distance = list(map(int, input("[w h d]> ").split(" ")))
        face.stop()
        face = Face(color="seagreen", eye_height=height, eye_width=width, distance=distance)
        face.start()

    # Margin test
    face.look("left")
    time.sleep(2)
    face.look("right")
    time.sleep(2)
    face.look("left")
    time.sleep(2)
    face.look("right")
    time.sleep(2)
    try:
        while True:
            face.move_to(*face.random_within_bounds())
            time.sleep(random.randint(3, 5))
    except KeyboardInterrupt:
        face.stop()
