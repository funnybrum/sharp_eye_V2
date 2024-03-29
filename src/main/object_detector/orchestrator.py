import glob
import json
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
        self._video_root = config['snapshots']['location']

    def loop(self):
        unprocessed_files = 0
        for video_file in sorted(glob.glob("%s/**/*.mp4" % self._video_root)):
            if self._metadata_store.get_metadata(video_file) is not None:
                continue

            try:
                with open(video_file[:-3] + "json", 'r') as meta_in_file:
                    input_metadata = json.load(meta_in_file)
            except:
                input_metadata = None

            frames_with_objects = self._process_video_file(video_file, input_metadata)
            if frames_with_objects is None:
                unprocessed_files += 1
                continue

            scores = self._get_adjusted_objects_scores(frames_with_objects)
            self._metadata_store.store_metadata(video_file, scores)
            if frames_with_objects:
                for processor in self._processors:
                    processor.process(video_file, scores, frames_with_objects)

        return unprocessed_files

    def _process_video_file(self, video_file, input_metadata):
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

            # Generate ROI sub-frame
            if input_metadata:
                roi = self._get_region_of_interest(frame, input_metadata[frames])
            else:
                roi = (0, 0, frame.shape[1], frame.shape[0])
            frames += 1

            if roi is None:
                continue

            roi_image = self._extract_roi_image(frame, roi)

            # Perform object detection
            objects = self._detector.detect(roi_image)

            # Identify objects that are with sufficient confidence.
            objects = [o for o in objects if o['confidence'] >= self._confidence_threshold]

            # Map ROI image coordinates to frame coordinates
            self._map_object_coordinates(frame, roi, objects)

            if objects:
                frames_with_objects.append({
                    'frame': frame,
                    'objects': objects
                })

        if frames == 0:
            log(f"Failed to process {video_file}, is the file still being written to?")
            return None

        log("Processed %s with %s frames in %d seconds" % (
            video_file, frames, time() - start))

        return frames_with_objects

    def _get_region_of_interest(self, frame, frame_metadata):  # noqa
        """
        Get the region of interest from the frame metadata. If no region of interest is identified return None
        """
        frame_motion = frame_metadata["motion"]
        if frame_motion["w"] == 0 or frame_motion["h"] == 0:
            # Skip frames without motion in them.
            return None

        image_width, image_height = frame.shape[1], frame.shape[0]

        x = frame_motion["x"]
        y = frame_motion["y"]
        w = frame_motion["w"]
        h = frame_motion["h"]

        # Ensure that the area is square
        if h > w:
            x -= round((h - w) / 2)
            w = h
        elif w > h:
            y -= round((w - h) / 2)
            h = w

        # Extend a bit the area without going outside the image
        if w < min(image_width, image_height) * 0.6:
            x = round(x - w * 0.25)
            y = round(y - h * 0.25)
            w = round(w * 1.5)
            h = round(h * 1.5)
        elif w < min(image_width, image_height) * 0.75:
            x = round(x - w * 0.1)
            y = round(y - h * 0.1)
            w = round(w * 1.2)
            h = round(h * 1.2)

        # Fit the area in the image
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x + w > image_width:
            w = image_width - x
        if y + h > image_height:
            h = image_height - y

        assert x >= 0 and y >= 0 and x + w <= image_width and y + h <= image_height, "Invalid ROI"

        return x, y, w, h

    def _extract_roi_image(self, frame, roi):  # noqa
        roi_x, roi_y, roi_w, roi_h = roi
        return frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]

    def _map_object_coordinates(self, frame, roi, objects):
        # Image is passed in the default scale, so there is no scale factor. But there is offset because we are using
        # a portion of the frame.
        x_offset, y_offset, _, _ = roi
        for obj in objects:
            obj["xmin"] += x_offset
            obj["xmax"] += x_offset
            obj["ymin"] += y_offset
            obj["ymax"] += y_offset

    def _get_adjusted_objects_scores(self, frames_with_objects):  # noqa
        scores = {}
        detection_counts = {}

        for f in frames_with_objects:
            for obj in f['objects']:
                obj_type = obj['name']
                obj_score = obj['confidence']
                if obj_type not in scores:
                    scores[obj_type] = 0
                    detection_counts[obj_type] = 0
                scores[obj_type] += obj_score
                detection_counts[obj_type] += 1

        for obj_type, score in scores.items():
            scores[obj_type] = round(score / len(frames_with_objects), 2)

        confidence_threshold = config['object_detection']['metadata_threshold']
        detection_count_threshold = config['object_detection']['detection_count_threshold']
        scores = {k: v for k, v in scores.items() if
                  v >= confidence_threshold and
                  detection_counts[k] >= detection_count_threshold}

        return scores
