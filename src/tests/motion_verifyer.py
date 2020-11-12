import cv2
import os

from fnmatch import fnmatch
import numpy

from lib import config

CAM = 1
DAY = 2
START_FRAME = 0
END_FRAME = 4000
IMAGES_DIR = '/media/brum/storage/snapshots/day%s/camera%s/' % (DAY, CAM)
MOTION_MASK = '/media/brum/dev/python/projects/surveillance/resources/cam%s_mask.png' % CAM
MOTION_INFO_FILE = 'data_d%s_c%s.txt' % (DAY, CAM)
LAST_IMAGE = ''
WRONG_DETECTIONS = 0

detected_motion = {}

def load():
    data = {}

    lines = []
    with open(MOTION_INFO_FILE, 'r') as in_file:
        for line in in_file:
            lines.append(line)

    for line in lines[START_FRAME:END_FRAME]:
        line = line.rstrip()
        tokens = line.split(':')
        if 'True' == tokens[1]:
            data[tokens[0]] = True
        elif 'False' == tokens[1]:
            data[tokens[0]] = 'False'
        else:
            data[tokens[0]] = None

    return data

REAL_DATA = load()


def init_config():
    config['motion'] = {}
    config['motion']['camera_retry_count'] = 1
    config['motion']['dc_pixels'] = 200
    config['motion']['dc_percent'] = 10
    config['motion']['sc_pixels'] = 2000
    config['motion']['sc_percent'] = 50
    config['motion']['mask'] = MOTION_MASK

    if CAM == 1:
        config['motion']['threshold'] = 64
        config['motion']['history'] = 16
    else:
        config['motion']['threshold'] = 64
        config['motion']['history'] = 16


def create_cam():

    class Cam:

        def __init__(self):
            image_files = []
            for image_file in sorted(os.listdir(IMAGES_DIR)):
                if fnmatch(image_file, 'frame*jpg'):
                    image_files.append(IMAGES_DIR + image_file)

            self.image_files = iter(image_files[START_FRAME:END_FRAME])

        def snapshot_img(self, retries):
            if WRONG_DETECTIONS >= 30:
                raise StopIteration
            global LAST_IMAGE
            LAST_IMAGE = self.image_files.next()
            img = cv2.imread(LAST_IMAGE)
            img = cv2.resize(img, (0, 0), fx=4, fy=4)
            return img

    return Cam()


def on_action(motion_frame, snapshot, prev_snapshot, data):
    if data['last_no_motion'] and data['motion_length'] == 1:
        key = LAST_IMAGE[-14:]
        detected_motion[key] = data
        print('%s-%s: %s, %s, %s' % (key, REAL_DATA[key], data['motion_rect'], data['non_zero_pixels'], data['non_zero_percent']))
        global WRONG_DETECTIONS
        if REAL_DATA[key] != True:
            WRONG_DETECTIONS += 1
            # print(LAST_IMAGE[-14:])
#             to_show = numpy.hstack((
#                 cv2.resize(prev_snapshot, (0, 0), fx=0.33, fy=0.33),
#                 cv2.resize(snapshot, (0, 0), fx=0.33, fy=0.33),
#                 cv2.resize(motion_frame, (0, 0), fx=0.66, fy=0.66),
#             ))
#             cv2.imshow('motion', to_show)
#             cv2.waitKey(1000)
#             cv2.destroyWindow('motion')


def test(detector):
    global WRONG_DETECTIONS
    WRONG_DETECTIONS = 0
    detected_motion.clear()
    try:
        while True:
            detector.check_next_frame()
    except StopIteration:
        pass

    missed = 0
    wrong = 0
    detected = 0
    non_relevant = 0
    missed_str = ''
    wrong_str = ''
    non_relevant_str = ''
    for key in detected_motion:
        if REAL_DATA[key] == True:
            detected += 1
        elif REAL_DATA[key] == False:
            wrong += 1
            wrong_str += key + ';'
        else:
            non_relevant += 1
            non_relevant_str += key + ';'
    for key in sorted(REAL_DATA):
        if REAL_DATA[key] == True:
            if key not in detected_motion:
                missed += 1
                missed_str += key + ';'

    print('%s,%s,%s: %s,%s,%s\t%s\t%s' % (
        detector.MOTION_THRESHOLD,
        detector.MOTION_HISTORY,
        detector.NOISE_FILTERING_RECT,
        detected,
        wrong,
        non_relevant,
        missed_str,
        non_relevant_str))
    # if wrong == 0 or wrong > detector:
    #     return 'skip'

if __name__ == '__main__':
    init_config()
    print('MOTION_THRESHOLD,MOTION_HISTORY,DETECTED,WRONG')

    # from sharp_eye.detector import MotionDetector
    # for MOTION_HISTORY in [16]:
    #     for MOTION_THRESHOLD in [64]:
    #         for MIN_MOTION_SIZE in [(2, 3), (3, 5), (4, 6)]:
    #             MotionDetector.MOTION_THRESHOLD = MOTION_THRESHOLD
    #             MotionDetector.MOTION_HISTORY = MOTION_HISTORY
    #             MotionDetector.MIN_MOTION_SIZE = MIN_MOTION_SIZE
    #             cam = create_cam()
    #             detector = MotionDetector(cam, on_action)
    #             if test(detector) == 'skip':
    #                 break

    from sharp_eye.detector import MotionDetector
    cam = create_cam()
    detector = MotionDetector(cam, on_action)
    test(detector)
