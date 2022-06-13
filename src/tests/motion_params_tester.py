import os

if not os.environ.get('APP_CONFIG'):
    os.environ['APP_CONFIG'] = '/brum/dev/sharp_eye/src/resources/cam1.yaml'

import cv2
from sharp_eye.detector import MotionDetector
from lib import config
import time

def getCurrentMemoryUsage():
    ''' Memory usage in kB '''

    with open('/proc/self/status') as f:
        memusage = f.read().split('VmRSS:')[1].split('\n')[0][:-3]

    return int(memusage.strip())/1000.0


def create_cam():
    class Cam:
        def __init__(self):
            self.count = 1

        def snapshot_img(self):
            filename = "/media/brum/b2478a80-d995-4ab3-8521-e4599cc787a4/snapshots/camera1/{:06d}.jpg".format(
                self.count)
            try:
                if self.count >= 600:
                    raise StopIteration
                img = cv2.imread(filename)
            except:
                cv2.destroyAllWindows()
                return None
            self.count += 1
            # if self.count % 100 == 0:
            #     print("Memory usage: %s" % getCurrentMemoryUsage())
            return img

    return Cam()


def get_event_tracker():
    class EventTracker:

        def __init__(self):
            self.invalid = 0
            self.missed = 0

        def track_frame(self, frame_obj):
            invalid_delay = 0
            if 301 <= frame_obj.index <= 364:
                if not frame_obj.motion:
                    self.missed += 1
            else:
                if frame_obj.motion and frame_obj.index > 1:
                    invalid_delay = 5000
                    self.invalid += 1

            # cv2.imshow("Frame", cv2.resize(frame_obj.frame, (0, 0), fx=0.25, fy=0.25))
            # cv2.putText(frame_obj.motion_mask, "frame {}, motion {}".format(frame_obj.index, frame_obj.motion), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (128, 255, 128), 2)
            # cv2.imshow("mask", frame_obj.motion_mask)
            # if frame_obj.motion:
            #     cv2.waitKey(100 + invalid_delay)
            # else:
            #     cv2.waitKey(1 + invalid_delay)

    return EventTracker()


if __name__ == "__main__":
    print("hi\tth\tbgr\tmis\tinv\t\tsec")
    config['motion']['mask'] = '/brum/dev/sharp_eye/src/resources/img/cam1_mask.png'

    for history in [64, 128]:
        for threshold in [64, 128, 196]:
            for bg_ration in [0.2, 0.5, 0.8]:
                for shadow in [0.5]:
                    start = time.time()
                    config['motion']['threshold'] = threshold
                    config['motion']['history'] = history
                    event_tracker = get_event_tracker()
                    detector = MotionDetector(create_cam(), event_tracker, None)
                    detector.detector.setShadowThreshold(shadow)
                    detector.detector.setDetectShadows(True)
                    detector.detector.setBackgroundRatio(bg_ration)
                    detector.run()
                    print("%d\t%d\t%d\t%d\t%d\t\t%d" % (history, threshold, bg_ration*100, event_tracker.missed, event_tracker.invalid, time.time()-start))