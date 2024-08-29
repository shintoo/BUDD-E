#!/usr/bin/python
# -*- coding: UTF-8 -*-
#import chardet
import os
import spidev
import sys 
import time
import logging
from random import randint
from datetime import datetime
import spidev as SPI

from gc9a01 import GC9A01
from PIL import Image,ImageDraw,ImageFont

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

print(f"Max SPI speed: {spidev.SpiDev(0,0).max_speed_hz}")

# Raspberry Pi pin configuration:
RST = 27
DC = 25
BL = 18
bus = 0 
device = 0
logging.basicConfig(level=logging.DEBUG)
try:
    # display with hardware SPI:
    ''' Warning!!!Don't  creation of multiple displayer objects!!! '''
    display = GC9A01(spi=SPI.SpiDev(bus, device),spi_freq=80000000,rst=RST,dc=DC,bl=BL)
    #disp = LCD_1inch28.LCD_1inch28()
    # Initialize library.
    display.Init()
    # Clear display.
    display.clear()
    #Set the backlight to 100
    display.bl_DutyCycle(50)

    speed = 5

    frame = Image.new("RGB", (display.width, display.height), "BLACK")
    display.ShowImage(frame)
    draw = ImageDraw.Draw(frame)
    prev = datetime.now()
    x = 40
    y = 100
    x_speed = 0
    y_speed = 0
    eye_width = 40
    eye_height = 60
    eye_distance = eye_width + 40
    blink_total = 3
    gaze_total = 6
    gaze_left = gaze_right = gaze_up = gaze_down = False
    blink = False
    opening = False
    closing = False
    gazing = False
    while True:
        now = datetime.now()
        delta = (now - prev).total_seconds()

        if not closing and not opening:
            blink_total -= delta
            if blink_total <= 0: 
                closing = True
        if closing and eye_height <= 7:
            opening = True
            closing = False
        if opening and eye_height >= 60:
            opening = False 
            blink_total = randint(3, 7)
            closing = False
        if opening:
            eye_height += 10 * (delta / 0.0333)
        if closing:
            eye_height -= 10 * (delta / 0.0333)
        if eye_height > 60:
            eye_height = 60

        if not gazing:
            gaze_total -= delta
            if gaze_total <= 0:
                gazing = True
                x_speed = randint(3 if gaze_right else -7, -3 if gaze_left else 7)
                y_speed = randint(3 if gaze_up else -7, -3 if gaze_down else 7)
                gaze_right = gaze_left = gaze_up = gaze_down = False
                gaze_total = randint(3,5)
        

        draw.rectangle((0, 0, 239, 239), fill=(0, 0, 0, 0))
        #draw.circle(xy=(x, 120), radius=45, fill=(0x1f, 0x91, 0xaf, 120))
        draw.rounded_rectangle(((x, y-(eye_height/2)), (x+eye_width, y+(eye_height/2))), 12, fill=(0x1f, 0x91, 0xaf, 120))
        draw.rounded_rectangle(((x+eye_distance, y-eye_height/2), (x+eye_width+eye_distance, y+(eye_height/2))), 12, fill=(0x1f, 0x91, 0xaf, 120))

        display.ShowImage(frame)
        prev = now
        print(f"{closing=}, {opening=}, {eye_height}, {x_speed=}, {y_speed=}, {gazing=}, {gaze_total=}")


        x = x + x_speed * (delta / 0.0333)
        y = y + y_speed * (delta / 0.0333)
        if gazing:
            if x > 200 - eye_width - eye_distance:
                x = 200 - eye_width - eye_distance
                x_speed = 0
                y_speed =  0
                gazing = False
                gaze_left = True
            elif x < 40:
                x = 40
                x_speed = 0
                y_speed = 0
                gazing = False
                gaze_right = True
            if y > 220 - eye_height:
                y = 220 - eye_height
                y_speed = 0
                x_speed = 0
                gazing = False
                gaze_down = True
            elif y < 60:
                y = 60 
                y_speed = 0
                x_speed = 0 
                gazing = False
                gaze_up = True

    display.module_exit()
    logging.info("quit:")
except IOError as e:
    logging.info(e)    
except KeyboardInterrupt:
    display.module_exit()
    logging.info("quit:")
    exit()
