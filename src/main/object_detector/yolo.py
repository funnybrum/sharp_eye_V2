import logging
import os
import torch
import warnings

from lib import config


class Detector(object):
    def __init__(self):
        self._yolo = None

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

    def detect(self, image):
        yolo_result = self._yolo([image])
        result = yolo_result.pandas().xyxy[0].to_dict(orient="records")
        return result
