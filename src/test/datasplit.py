import cv2
import os
import csv
from ast import literal_eval
from fnmatch import fnmatch

DIR = '/media/brum/storage/test/'

with open(DIR + 'incorrect.csv', 'w') as incorrect, open(DIR + 'correct.csv', 'w') as correct:
    incorrect_csv = csv.writer(incorrect)
    correct_csv = csv.writer(correct)

    incorrect_csv.writerow(['height', 'width', 'non_zero_percent', 'non_zero_pixels'])
    correct_csv.writerow(['height', 'width', 'non_zero_percent', 'non_zero_pixels'])

    for image_file in sorted(os.listdir(DIR)):
        if fnmatch(image_file, 'ff*jpg'):
            image = cv2.imread(DIR + image_file)

            with open(DIR + image_file.replace('.jpg', '.txt')) as json_file:
                data = literal_eval(json_file.read())
                print(data)


            cv2.imshow('image', cv2.resize(image, (0, 0), fx=0.5, fy=0.5))
            char = cv2.waitKey(0)

            if ord('y') == char:
                correct_csv.writerow([data['h'], data['w'], data['non_zero_percent'], data['non_zero_pixels']])
            elif ord('n') == char:
                incorrect_csv.writerow([data['h'], data['w'], data['non_zero_percent'], data['non_zero_pixels']])



