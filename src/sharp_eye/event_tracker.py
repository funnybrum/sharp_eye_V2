from lib import config

import subprocess


class EventTracker(object):
    """
    Combine multiple frames in an event. Based on the event specifics decide if this is a motion event that should
    trigger an alert.

    The goal is to reduce the noise level with highly sensitive motion detection. One example filtering rule is that a
    motion should trigger an alert only if there are 5 consecutive motion frames. Another example is tha there should be
    at least 6 frames with motion in the last 10 frames.
    """
    def __init__(self, on_alert, snapshot_tracker):
        self.alert_callback = on_alert
        self.snapshot_tracker = snapshot_tracker
        self.motion_history = [-1000]
        self.last_alert_sequence_start_frame = -1000

        self.min_no_motion_gap = config['event_tracker']['min_no_motion_gap']
        self.lookback_frames = config['event_tracker']['history_frame_count']
        self.lookback_motion_threshold = config['event_tracker']['motion_events_threshold']

    def track_frame(self, frame):
        self.snapshot_tracker.process_frame(frame)

        if frame.motion:
            self._on_motion_actions()

        # If this is a motion sequence that has passed the sequence detecting
        # conditions (or in other words - has triggered an alert) and it has
        # not finished due to a gap with no-motion frames then this is ongoing
        # motion.
        ongoing_motion = \
            self.last_alert_sequence_start_frame == self.motion_history[0] and \
            frame.index - self.motion_history[-1] <= self.min_no_motion_gap

        if ongoing_motion:
            self._on_motion_sequence_actions()

        if not frame.motion:
            return

        if frame.index - self.motion_history[-1] > self.min_no_motion_gap:
            # This is a new motion sequence. There has been a gap full of
            # no-motion frames and we have a new motion frame.
            self.motion_history = [frame.index]
        else:
            self.motion_history.append(frame.index)

        if self.last_alert_sequence_start_frame == self.motion_history[0]:
            # An alert was already sent for this sequence.
            return

        motion_frames = len(
            [x for x in self.motion_history if x > frame.index - self.lookback_frames]
        )

        if motion_frames > self.lookback_motion_threshold:
            self._on_motion_sequence_actions()
            self.last_alert_sequence_start_frame = self.motion_history[0]
            self.alert_callback(frame)

    def _on_motion_actions(self):
        if 'automation' in config and 'on_motion_frame_script' in config['automation']:
            subprocess.Popen([config['automation']['on_motion_frame_script']], shell=True)
        self.snapshot_tracker.on_single_motion_frame()

    def _on_motion_sequence_actions(self):
        if 'automation' in config and 'on_motion_sequence_script' in config['automation']:
            subprocess.Popen([config['automation']['on_motion_sequence_script']], shell=True)
        self.snapshot_tracker.on_sequence_motion_frame()
