import logging
import os
from ultralytics import YOLO
import warnings

from lib import config


class Detector(object):
    def __init__(self):
        self._yolo = None

    def init(self):
        logging.basicConfig(level=logging.WARNING)

        warnings.filterwarnings("ignore")

        base_path = os.path.dirname(os.path.abspath(__file__))

        self._yolo = YOLO(os.path.join(base_path, config['yolo']['pretrained_model']), task='detect')

    def detect(self, image):
        yolo_result = self._yolo([image], verbose=False)[0]
        objects = []
        for box in yolo_result.boxes:
            objects.append({
                "name": yolo_result.names[box.cls[0].item()],
                "confidence": round(box.conf[0].item(), 2),
                "xmin": int(box.xyxy[0][0]),
                "ymin": int(box.xyxy[0][1]),
                "xmax": int(box.xyxy[0][2]),
                "ymax": int(box.xyxy[0][3]),
            })
        return objects
