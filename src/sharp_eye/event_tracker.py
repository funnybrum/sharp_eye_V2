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
    def __init__(self, on_alert):
        self.alert_callback = on_alert
        self.motion_history = [-1000]
        self.last_alert_sequence_start_frame = -1

        self.min_no_motion_gap = config['event_tracker']['min_no_motion_gap']
        self.lookback_frames = config['event_tracker']['history_frame_count']
        self.lookback_motion_threshold = config['event_tracker']['motion_events_threshold']

    def on_motion(self, motion_frame, snapshot, prev_snapshot, data):
        if 'automation' in config and 'on_motion_frame_script' in config['automation']:
            subprocess.Popen([config['automation']['on_motion_frame_script']], shell=True)

        if data['frame_count'] - self.motion_history[-1] > self.min_no_motion_gap:
            # This is a new motion sequence.
            self.motion_history = [data['frame_count']]
        else:
            self.motion_history.append(data['frame_count'])

        if self.last_alert_sequence_start_frame == self.motion_history[0]:
            # An alert was already sent for this sequence
            return

        motion_frames = len(
            [x for x in self.motion_history if x > data['frame_count'] - self.lookback_frames]
        )

        if motion_frames > self.lookback_motion_threshold:
            self.last_alert_sequence_start_frame = self.motion_history[0]
            self.alert_callback(motion_frame, snapshot, prev_snapshot, data)
