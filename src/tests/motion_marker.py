from __future__ import absolute_import

import cv2
import os

from fnmatch import fnmatch


CAM = 2
DAY = 0
IMAGES_DIR = '/media/brum/storage/snapshots/camera%s/' % CAM
MOTION_MASK = '/media/brum/dev/python/projects/surveillance/resources/cam%s_mask.png' % CAM
MOTION_INFO_FILE = 'data_d%s_c%s.txt' % (DAY, CAM)
MOTION_MASK = cv2.imread('/media/brum/dev/python/projects/surveillance/resources/cam%s_mask.png' % CAM)
MOTION_MASK = cv2.resize(MOTION_MASK, (0, 0), fx=0.25, fy=0.25)
MOTION_MASK = cv2.cvtColor(MOTION_MASK, cv2.COLOR_BGR2GRAY)

def save(data):
    with open(MOTION_INFO_FILE, 'w') as out_file:
        for key in sorted(data):
            out_file.write(key + ':' + str(data[key]) + '\n')


def load():
    data = {}
    with open(MOTION_INFO_FILE, 'r') as in_file:
        for line in in_file:
            line = line.rstrip()
            tokens = line.split(':')
            data[tokens[0]] = 'True' == tokens[1]

    return data


def process_images(data):
    image_files = []
    for image_file in sorted(os.listdir(IMAGES_DIR)):
        if fnmatch(image_file, 'frame*jpg'):
            image_files.append(image_file)

    index = 0
    while index < len(image_files):
        image_file = image_files[index]

        if image_file in data:
            index += 1
        else:
            break

    while index < len(image_files):
        image_file = image_files[index]

        image = cv2.imread(IMAGES_DIR + image_file)
        image = cv2.bitwise_and(image, image, mask=MOTION_MASK)
        cv2.putText(image, image_file, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (128, 255, 128), 2)
        cv2.imshow('image', cv2.resize(image, (0, 0), fx=2, fy=2))
        char = cv2.waitKey(0)

        processed = False
        motion = False
        while not processed:
            if ord('u') == char:
                processed = True
                motion = None
            if ord('y') == char:
                processed = True
                motion = True
            if ord('n') == char:
                processed = True
                motion = False
            if ord('p') == char:
                index -= 2
                processed = True
            if ord('e') == char:
                index += 10000
                processed = True
        index += 1
        data[image_file] = motion
        if index % 20 == 0:
            save(data)

    return data

if __name__ == '__main__':
    try:
        data = load()
    except IOError:
        data = {}
    data = process_images(data)
    save(data)
