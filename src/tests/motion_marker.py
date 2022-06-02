from __future__ import absolute_import

import cv2
import os
import ast
import csv

from fnmatch import fnmatch


CAM = 1
IMAGES_DIR = '/media/brum/b2478a80-d995-4ab3-8521-e4599cc787a4/sharp_eye/camera%s/' % CAM
MOTION_INFO_FILE = 'data_c%s.txt' % CAM


def save(data):
    with open(MOTION_INFO_FILE, 'w') as out_file:
        writer = csv.DictWriter(
            out_file,
            fieldnames=['real_motion', 'non_zero_pixels', 'non_zero_percent', 'w', 'h', 'file'],
            extrasaction='ignore')
        writer.writeheader()
        for key in data:
            row = data[key]
            row['file'] = key
            writer.writerow(row)

def load():
    data = {}
    # with open(MOTION_INFO_FILE, 'r') as in_file:
    #     for line in in_file:
    #         line = line.rstrip()
    #         tokens = line.split(':')
    #         data[tokens[0]] = 'True' == tokens[1]
    #
    return data


def process_images(data):
    image_files = os.listdir(IMAGES_DIR)
    image_files = [x for x in image_files if "ff_2022" in x and "jpg" in x]
    image_files = sorted(image_files, key=lambda x: int(x.split('-')[-1][:-4]))

    index = 0
    while index < len(image_files):
        image_file = image_files[index]

        image = cv2.imread(IMAGES_DIR + image_file)
        with open(IMAGES_DIR + image_file[:-3] + 'txt', "r") as f:
            img_data = ast.literal_eval(f.read())
        cv2.putText(image, image_file, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (128, 255, 128), 2)

        x = int(img_data['x'] * 4)
        y = int(img_data['y'] * 4)
        w = int(img_data['w'] * 4)
        h = int(img_data['h'] * 4)

        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow('image', cv2.resize(image, (0, 0), fx=0.5, fy=0.5))

        char = cv2.waitKey(0)

        processed = False
        motion = False
        while not processed:
            if ord('u') == char:
                processed = True
                motion = "undef"
            if ord('y') == char:
                processed = True
                motion = "yes"
            if ord('n') == char:
                processed = "no"
                motion = False
            if ord('c') == char:
                processed = "cat"
                motion = False
            if ord('p') == char:
                index -= 2
                processed = True
            if ord('e') == char:
                index += 10000
                processed = True
        index += 1
        data[image_file] = img_data
        data[image_file]["real_motion"] = motion
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
