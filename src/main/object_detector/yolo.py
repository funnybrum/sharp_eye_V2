import logging
import os
import torch
import warnings

from lib import config


class Detector(object):
    def __init__(self):
        self._yolo = None
        self._yolo_tiny = None

    def init(self):
        logging.basicConfig(level=logging.WARNING)

        warnings.filterwarnings("ignore")

        base_path = os.path.dirname(os.path.abspath(__file__))

        self._yolo = torch.hub.load(
            os.path.join(base_path, config['yolo']['model_source']),
            'custom',
            os.path.join(base_path, config['yolo']['pretrained_model']),
            source='local',
            trust_repo=True,
            skip_validation=True,
            verbose=False)

        self._yolo_tiny = torch.hub.load(
            os.path.join(base_path, config['yolo']['model_source']),
            'custom',
            os.path.join(base_path, config['yolo']['pretrained_model_tiny']),
            source='local',
            trust_repo=True,
            skip_validation=True,
            verbose=False)

    def detect(self, image, fast=False):
        model = self._yolo_tiny if fast else self._yolo
        yolo_result = model([image])
        result = yolo_result.pandas().xyxy[0].to_dict(orient="records")
        return result
