import glob
import os
import shutil

import cv2

from lib import config
from lib.log import log


class Orchestrator(object):
    def __init__(self, detector, processors):
        """
        :param detector: Object with .detect method that takes a image end return detected objects.
        :param processors: List of processors for the detected objects.
        """
        self._detector = detector
        self._processors = processors
        self._input_path = config['object_detection']['path']
        self._fast_model_disk_utilization_threshold = config['object_detection']['fast_model_disk_utilization_threshold']
        self._confidence_threshold = config['object_detection']['confidence_threshold']

    def loop(self):
        for descriptor_file in sorted(glob.glob('%s/**/*.txt' % self._input_path)):
            descriptor = os.path.split(descriptor_file)[-1][:-4]
            log("Processing %s" % descriptor)
            result = self._process_motion_sequence(descriptor_file)
            if result:
                for processor in self._processors:
                    processor.process(descriptor, result)

    def _should_use_fast_model(self):
        total, used, _ = shutil.disk_usage(self._input_path)
        disk_utilization = used / total
        return disk_utilization >= self._fast_model_disk_utilization_threshold

    def _process_motion_sequence(self, descriptor):
        """
        Process motion sequence by looking at the video generation file used by ffmpeg.

        Result is list of frames containing objects. For each item in the list there are two properties:
        1) frame - the CV2 image
        2) objects - the list of objects with the following metadata:
          - 'name' that is the object type (person, dog, ...)
          - 'confidence' containing the confidence value
          - 'ymin', 'ymax', 'xmin', 'xmax' specifying the object bounding box in the frame

        :param descriptor: video generation files with frame sequence
        :return: list of frames with detected objects
        """
        with open(descriptor, 'r') as descriptor_file:
            frames = descriptor_file.readlines()

        sequence_folder = os.path.dirname(descriptor)

        frames = [os.path.join(sequence_folder, os.path.split(f[6:-2])[-1]) for f in frames if 'file' in f]
        use_fast_model = self._should_use_fast_model()

        result = []
        for f in frames:
            img = cv2.imread(f)
            objects = self._detector.detect(img, fast=use_fast_model)
            objects = [o for o in objects if o['confidence'] >= self._confidence_threshold]
            if objects:
                result.append({
                    'frame': img,
                    'objects': objects
                })

            # Clean up processed frames
            os.remove(f)

        # Clean up the processed motion sequence descriptor
        os.remove(descriptor)

        return result
