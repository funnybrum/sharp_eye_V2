import glob
import os
from time import time

import cv2

from lib import config
from lib.log import log


class Orchestrator(object):
    def __init__(self, detector, metadata_store, processors):
        """
        :param detector: Object with .detect method that takes a image end return detected objects.
        :param processors: List of processors for the detected objects.
        """
        self._detector = detector
        self._metadata_store = metadata_store
        self._processors = processors
        self._confidence_threshold = config['object_detection']['confidence_threshold']

    def loop(self):
        for video_file in sorted(glob.glob('/snapshots/**/*.mp4')):
            if self._metadata_store.get_metadata(video_file) is not None:
                continue

            frames_with_objects = self._process_video_file(video_file)

            self._metadata_store.store_metadata(video_file, frames_with_objects)
            if frames_with_objects:
                for processor in self._processors:
                    processor.process(video_file, frames_with_objects)

    def _process_video_file(self, video_file):
        """
        Process video file through the object detector and generate list of frames with motion.

        Result is list of frames containing objects. For each item in the list there are two properties:
        1) frame - the CV2 image
        2) objects - the list of objects with the following metadata:
          - 'name' that is the object type (person, dog, ...)
          - 'confidence' containing the confidence value
          - 'ymin', 'ymax', 'xmin', 'xmax' specifying the object bounding box in the frame
        """
        log("Processing %s" % video_file)
        frames = 0
        frames_with_objects = []
        start = time()
        capture = cv2.VideoCapture(video_file)
        while True:
            ret, frame = capture.read()
            if not ret:
                break

            frames += 1
            objects = self._detector.detect(frame)
            objects = [o for o in objects if o['confidence'] >= self._confidence_threshold]
            if objects:
                frames_with_objects.append({
                    'frame': frame,
                    'objects': objects
                })

        log("Processed %s with %s frames in %d seconds" % (
            video_file, frames, time() - start))

        return frames_with_objects
