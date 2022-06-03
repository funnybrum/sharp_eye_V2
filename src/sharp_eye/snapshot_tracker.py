from lib import config


class SnapshotTracker(object):
    def __init__(self):
        self._frames = []

    def process_frame(self, frame):
        if config['motion']['snapshot_history'] != 'full':
            return

    def process_single_motion_frame(self, frame):
        if config['motion']['snapshot_history'] != 'motion_frame':
            return

    def process_sequence_motion_frame(self, frame):
        if config['motion']['snapshot_history'] != 'motion_sequence':
            return
