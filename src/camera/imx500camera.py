import time
from datetime import datetime
from threading import Thread, Event
import traceback

import cv2
from picamera2 import Picamera2
from picamera2.devices import IMX500
from picamera2.devices.imx500 import NetworkIntrinsics, postprocess_nanodet_detection

DEFAULT_OBJECT_EXPIRY=6

class DetectedObject:
    def __init__(self, label, centroid, expiry=DEFAULT_OBJECT_EXPIRY):
        self.label = label
        self.centroid = centroid
        self.expiry = expiry

    def __repr__(self):
        return f"<DetectedObject label={self.label} centroid={self.centroid} expiry={self.expiry}>"

class IMX500Camera:
    def __init__(self, model, labels_file=None, frame_rate=0.5)
        self._stop_event = Event()
        self.frame_rate = frame_rate
        self.model = model
        self._thread = None

        self.imx500 = IMX500(self.model)
        self.intrinsics = imx500.network_intrinsics
        self._detection_threshold = 0.55
        self._detection_iou = 0.55
        self._detected_objects = {}

        if intrinsics.inference_rate is None:
            intrinsics.inference_rate = 10
        if intrinsics.labels is None:
            if not labels_file:
                message = f"[Camera] Model {model} does not have labels bundled, please provided a labels file."
                print(message)
                raise ValueError(message)
            print(f"[Camera] Model intrinsics missing labels, loading from {labels_file}")
            with open(labels_file) as f:
                intrinsics.labels = f.read().splitlines()

        intrinsics.update_with_defaults()

        self._cam = Picamera2(imx500.camera_num)
        imx500.show_network_fw_progress_bar()

    def get_captured_objects(self):
        return self._detected_objects

    def start(self):
        print(f"Starting camera with {self.model=}, {self.frame_rate}...", end="", flush=True)
        config = picam2.create_still_configuration(main={"size": (640, 640)})
        self._cam.start(config)
        self.imx500.set_auto_aspect_ratio()

        def target():
            while not self._stop_event.is_set():
                self.capture_objects()
                time.sleep(1 / frame_rate)

        self._thread = Thread(target=target)
        self._thread.start()
        print(f"done")

    def stop(self):
        self._stop_event.set()
        self._cam.stop()

    def capture_file(self, filename):
        self._cam.capture_file(filename)

    def capture_objects(self):
        """Capture detections from camera and update self._detected_objects"""
        # Grab imx500 output, sans image, from sensor
        metadata = self._cam.capture_metadata()
        labels = get_labels()

        # Configs for bounding boxes
        bbox_normalization = intrinsics.bbox_normalization
        bbox_order = intrinsics.bbox_order
        max_detections = args.max_detections

        # Parse sensor outputs
        np_outputs = imx500.get_outputs(metadata, add_batch=True)
        input_w, input_h = imx500.get_input_size()
        if np_outputs is None:
            return

        # Get boxes, scores, categories based on config
        if intrinsics.postprocess == "nanodet":
            boxes, scores, categories = \
                postprocess_nanodet_detection(outputs=np_outputs[0], conf=self._detection_threshold, iou_thres=self._detection_iou,
                                            max_out_dets=max_detections)[0]
            from picamera2.devices.imx500.postprocess import scale_boxes
            boxes = scale_boxes(boxes, 1, 1, input_h, input_w, False, False)
        else:
            boxes, scores, categories = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0]
            if bbox_normalization:
                boxes = boxes / input_h

            if bbox_order == "xy":
                boxes = boxes[:, [1, 0, 3, 2]]
            boxes = np.array_split(boxes, 4, axis=1)
            boxes = zip(*boxes)

        # Build list of objects detected this frame
        detected_objects = [DetectedObject(labels[int(category)], centroid(box)) for category, box in zip(categories, boxes)]
        print(f"\tdetected {len(detected_objects)} objects this frame")

        self._add_new_objects(detected_objects)
        self._clean_detected_objects()

    def _add_new_objects(detected_objects):
        # Update expiry for all previously-tracked objects, and flag all other this-frame objects to be added to tracked objects
        for do in self._detected_objects:
            for ndo in detected_objects:
                if do.label == ndo.label and ndo.expiry:
                    do.expiry = DEFAULT_OBJECT_EXPIRY + 1
                    do.centroid = ndo.centroid
                    # Set expiry of the new detected object to 0 to flag it as non-new, to skip adding it below
                    ndo.expiry = 0

        # Add new this-frame objects to tracked objects
        self._detected_objects.extend([ndo for ndo in detected_objects if ndo.expiry])

    def _clean_detected_objects(self):
        """Update object expiries and remove expired detections"""
        for do in self._detected_objects.values():
            do.expiry -= 1

        self._detected_objects = { do.label: do for do in self._detected_objects if do.expiry >= 0]

 
@lru_cache
def get_labels():
    labels = intrinsics.labels

    if intrinsics.ignore_dash_labels:
        labels = [label for label in labels if label and label != "-"]
    return labels

def centroid(box):
    return (box[0] + (box[3] - box[0]) / 2, box[1] + (box[4] - box[1]) / 2)

if __name__ == "__main__":
    from sys import args

    model = args[1]
    frame_rate = 0.5 if len(args) == 2 else args[2]
    cam = IMX500Camera(model=model, frame_rate=frame_rate)
    cam.start()

    try:
        while True:
            print(cam.get_captured_objects())
            time.sleep(1 / frame_rate)
    except KeyboardInterrupt as ki:
        cap.stop()

