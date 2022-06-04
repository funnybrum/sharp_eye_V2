import cv2
import os

from datetime import datetime

from lib import config


class SnapshotTracker(object):
    def __init__(self):
        self._frames = {}
        self._history_length = config['snapshots']['history']
        self._snapshot_folder = os.path.join(
            config['snapshots']['location'],
            config['identifier'])
        if not os.path.exists(self._snapshot_folder):
            os.mkdir(self._snapshot_folder)

    def process_frame(self, frame):
        self._frames[frame.index] = frame

        while len(self._frames) > self._history_length:
            self._frames.pop(next(iter(self._frames)))

        if config['snapshots']['type'] != 'full':
            return

        self._save_frame(frame.index, False)

    def on_single_motion_frame(self):
        if config['snapshots']['type'] != 'motion_frame':
            return

        index = self._frames.keys()[-1]
        self._save_frame(index)

    def on_sequence_motion_frame(self):
        if config['snapshots']['type'] != 'motion_sequence':
            return

        for index in iter(self._frames):
            self._save_frame(index)

        self._frames = {}

    def _save_frame(self, frame_index, full_data=True):
        frame_key = "%s-%s" % (datetime.now().strftime("%Y-%m-%d-%H-%M"), frame_index)
        frame = self._frames[frame_index]
        cv2.imwrite('%s/ff_%s.jpg' % (self._snapshot_folder, frame_key), frame.frame)

        if not full_data:
            return

        cv2.imwrite('%s/mk_%s.jpg' % (self._snapshot_folder, frame_key), frame.motion_mask)
        with open('%s/ff_%s.txt' % (self._snapshot_folder, frame_key), 'w') as ff_info:
            ff_info.write(str(frame.get_metadata()))
