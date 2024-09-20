import time
from datetime import datetime
from threading import Thread
import traceback

import cv2
from picamera2 import Picamera2

class Camera:
    def __init__(self, frame_rate=0.5, buffer_path="./.camera-photo.jpg"):
        self._cam = Picamera2()
        self._buffer_path = buffer_path
        self._last_image_time = None
        self.frame_rate = frame_rate
        self.running = False

        self._cam.preview_configuration.main.size = (1920, 1080)
        #self._cam.preview_configuration.transform.vflip = True
        self._cam.preview_configuration.transform.vflip = True
        self._cam.configure("preview")

        self._cam.start()
 
        cascade_path = "/usr/share/opencv4/lbpcascades/lbpcascade_frontalface.xml"
        self._cascade = cv2.CascadeClassifier(cascade_path)

    def latest_image(self):
        return self._buffer_path

    def shoot(self):
        self._cam.capture_file(self._buffer_path)
        self._last_image_time = datetime.now()

    def shoot_faces(self):
        img = self._cam.capture_array()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self._cascade.detectMultiScale(gray, 1.1, 3, 0, (10, 10))

        return faces

    def time_since_last_image(self):
        if not self._last_image_time:
            return float("inf")

        return (datetime.now() - self._last_image_time).total_seconds()

    def run(self):
        while self.running:
            self._cam.take_photo(self._buffer_path)
            time.sleep(1 / frame_rate)

if __name__ == "__main__":
    from PIL import Image

    print("Creating camera")
    cam = Camera(frame_rate=0.2)
    print("Camera created")
    running = True
    cmd = None

    fps = 3
    prev = datetime.now()

    try: 
        print("Starting test loop")
        while running:
            now = datetime.now()
            delta = (now - prev).total_seconds()
    
#            if delta < 1 / fps:
#                time.sleep((1 / fps) - delta)
    
    #        cmd = input("[take/quit]> ")
            print("Shooting... ", end="")
            #cam.shoot()
            #faces = cam.face_locations()
            start = datetime.now()
            faces = cam.shoot_faces()
            end = datetime.now()
            elapsed = (end - start).total_seconds()
            print(faces, end="")
            print(f" - {elapsed}s")
            prev = now
            #match cmd:
            #    case "take":
            #        cam.shoot()
            #        faces = cam.face_locations()
            #        print(faces)
            #        
            #    case "quit":
            #        running = False
    except Exception as e:
        print(f"Caught {e}")
        traceback.print_exc() 
        cam._cam.stop()
