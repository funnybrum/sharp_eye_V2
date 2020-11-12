from __future__ import absolute_import

import cv2
import os
import numpy

from fnmatch import fnmatch
from itertools import cycle
from random import shuffle

from sharp_eye.detector import (
    MotionDetector,
    config
)

IMAGES = ['./images/img_no_motion_%s.jpg' % x for x in range(1, 15)]
shuffle(IMAGES)
IMAGES += ['./images/img_motion.jpg']

CAM = 1
IMAGES_DIR = '/home/brum/Downloads/md_day1/camera%s/' % CAM
MOTION_MASK = '/media/brum/dev/python/projects/surveillance/resources/cam%s_mask.png' % CAM
LAST_IMAGE = ''

USE_DIR = True


def init_config():
    config['motion'] = {}
    config['motion']['camera_retry_count'] = 1
    config['motion']['dc_pixels'] = 150
    config['motion']['dc_percent'] = 6
    config['motion']['sc_pixels'] = 1000
    config['motion']['sc_percent'] = 33
    config['motion']['mask'] = MOTION_MASK


def create_cam():
    class Cam:
        def __init__(self):
            if USE_DIR:
                image_files = []
                for image_file in sorted(os.listdir(IMAGES_DIR)):
                    if fnmatch(image_file, 'ff*jpg'):
                        image_files.append(IMAGES_DIR + image_file)
            else:
                image_files = cycle(IMAGES)

            self.image_files = iter(image_files)

        def adjust_gamma(self, image, gamma=1.0):
            # build a lookup table mapping the pixel values [0, 255] to
            # their adjusted gamma values
            invGamma = 1.0 / gamma
            table = numpy.array([((i / 255.0) ** invGamma) * 255
                                 for i in numpy.arange(0, 256)]).astype("uint8")

            # apply gamma correction using the lookup table
            return cv2.LUT(image, table)

        def snapshot_img(self, retries):
            global LAST_IMAGE
            LAST_IMAGE = self.image_files.next()
            img = cv2.imread(LAST_IMAGE)
            return img

    return Cam()


def on_action(motion_frame, snapshot, prev_snapshot, data):
    if data['last_no_motion'] and data['motion_length'] == 1:
        print('Showing motion frame... %s -> %s' % (prev_snapshot[190:220, 475:540].mean(), snapshot[190:220, 475:540].mean()))
        print(data)
        cv2.imshow('image', motion_frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == '__main__':
    init_config()
    cam = create_cam()
    detector = MotionDetector(cam, on_action)
    try:
        while True:
            motion = detector.check_next_frame()
            if motion:
                print('Motion -> %s: %s' % (motion, LAST_IMAGE))
    except StopIteration:
        pass
a