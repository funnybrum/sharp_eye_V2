IN_FOLDER = '/home/brum/Downloads/md/images/camera1/'
OUT_FOLDER = '/home/brum/Downloads/md/images/camera1_x/'


import os
import cv2
import ast

for filename in  os.listdir(IN_FOLDER):
  if filename[:2] == 'ff' and filename[-4:] == '.jpg':
    img = cv2.imread(IN_FOLDER + filename)
    with open(IN_FOLDER + filename[:-4] + '.txt') as data_file:
      data = ast.literal_eval(data_file.read())

    motion = False

    if data['h'] > 10 and data['w'] > 10:
      if data['non_zero_pixels'] > 150 and data['non_zero_percent'] > 6:
        motion = True
      if data['non_zero_pixels'] > 1000 or data['non_zero_percent'] > 33:
        motion = True

    text = '%s: %s' % (motion, data)
    cv2.putText(img, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0 if motion else 255, 0, 255 if motion else 0), 2)
    cv2.rectangle(img, (data['x']*2, data['y']*2),
                       (data['x']*2 + data['w']*2, data['y']*2 + data['h']*2), (0, 255, 0), 2)
    cv2.imwrite(OUT_FOLDER + filename, img)

# cam 2 >88px or >40px & >40%