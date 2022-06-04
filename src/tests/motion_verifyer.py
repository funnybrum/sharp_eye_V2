import cv2
import os

if not os.environ.get('APP_CONFIG'):
    os.environ['APP_CONFIG'] = '/brum/dev/sharp_eye/src/resources/cam1.yaml'


from fnmatch import fnmatch
import numpy

from lib import config

CAM = 1
DAY = 2
START_FRAME = 1
END_FRAME = 4368
IMAGES_DIR = '/media/brum/b2478a80-d995-4ab3-8521-e4599cc787a4/sharp_eye/camera%s/' % CAM
MOTION_MASK = '/brum/dev/sharp_eye/src/resources/img/cam%s_mask.png' % CAM
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


def load_motion_data():
    REAL_DATA = {}
    # gap = config['motion']['min_no_motion_gap']
    gap = 0
    ranges = [range(313, 346 + gap), range(4161, 4222 + gap), range(4230, 4313 + gap)]
    for i in range(START_FRAME, END_FRAME):
        REAL_DATA[str(i)] = any([i in x for x in ranges])
    return REAL_DATA


REAL_DATA = load_motion_data()


def init_config():
    config['motion']['mask'] = MOTION_MASK
    config['motion']['sc_pixels'] = 2
    config['snapshot']['type'] = 'none'


def get_frame_index_from_filename(fn):
    return fn.split('-')[-1][:-4]


def create_cam():
    class Cam:
        def __init__(self):
            image_files = []
            for image_file in sorted(os.listdir(IMAGES_DIR), key=lambda x: int(get_frame_index_from_filename(x))):
                frame_index = int(get_frame_index_from_filename(image_file))
                if START_FRAME <= frame_index <= END_FRAME:
                    image_files.append(IMAGES_DIR + image_file)

            self.image_files = iter(image_files)
            self.count = 0

        def snapshot_img(self):
            if WRONG_DETECTIONS >= 30:
                raise StopIteration
            global LAST_IMAGE
            LAST_IMAGE = self.image_files.__next__()
            img = cv2.imread(LAST_IMAGE)
            # img = cv2.resize(img, (0, 0), fx=4, fy=4)
            self.count += 1
            # if self.count % 100 == 0:
            #     print("Processed %d" % self.count)
            return img

    return Cam()


def on_action(motion_frame, snapshot, prev_snapshot, data):
    if data['last_no_motion'] and data['motion_detected']:
        frame_index = get_frame_index_from_filename(LAST_IMAGE)
        key = frame_index
        detected_motion[key] = data
        global WRONG_DETECTIONS
        if REAL_DATA[key] != True:
            WRONG_DETECTIONS += 1

            print('%s, %s, %s, %s' % (key, data['motion_rect'], data['non_zero_pixels'], data['non_zero_percent']))

            # to_show = numpy.hstack((
            #     cv2.resize(prev_snapshot, (0, 0), fx=0.33, fy=0.33),
            #     cv2.resize(snapshot, (0, 0), fx=0.33, fy=0.33),
            #     cv2.resize(motion_frame, (0, 0), fx=0.66, fy=0.66),
            # ))
        cv2.imshow('motion', motion_frame)
        cv2.waitKey(3000)
        cv2.destroyWindow('motion')


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

    print('%s,%s,%s,%s,%s,%s,%s' % (
        detector.MOTION_THRESHOLD,
        detector.MOTION_HISTORY,
        detector.MIN_MOTION_SIZE,
        detector.NOISE_FILTERING_RECT,
        detected,
        wrong,
        missed))

    # if wrong == 0 or wrong > detector:
    #     return 'skip'


if __name__ == '__main__':
    init_config()
    load_motion_data()
    print('MOTION_THRESHOLD,MOTION_HISTORY,MIN_MOTION_SIZE,NOISE_FILTERING_RECT,DETECTED,WRONG,MISSED')

    from sharp_eye.detector import MotionDetector
    # for MOTION_HISTORY in [32]:
    #     for MOTION_THRESHOLD in [8, 16, 32, 64]:
    #         for MIN_MOTION_SIZE in [(4, 8)]:  # (16, 20)
    #             for NOISE_FILTERING_RECT in [(2, 3)]:
    #                 MotionDetector.MOTION_THRESHOLD = MOTION_THRESHOLD
    #                 MotionDetector.MOTION_HISTORY = MOTION_HISTORY
    #                 MotionDetector.MIN_MOTION_SIZE = MIN_MOTION_SIZE
    #                 MotionDetector.NOISE_FILTERING_RECT = NOISE_FILTERING_RECT
    #                 cam = create_cam()
    #                 detector = MotionDetector(cam, on_action)
    #                 if test(detector) == 'skip':
    #                     break

    from sharp_eye.detector import MotionDetector
    cam = create_cam()
    MotionDetector.MOTION_HISTORY = 32
    MotionDetector.MIN_MOTION_SIZE = (4, 8)
    detector = MotionDetector(cam, on_action)
    test(detector)

    for key in detected_motion.keys():
        if REAL_DATA[key]:
            data = detected_motion[key]
            data['valid'] = True
            print(data)

    for key in detected_motion.keys():
        if not REAL_DATA[key]:
            data = detected_motion[key]
            data['valid'] = False
            print(data)
