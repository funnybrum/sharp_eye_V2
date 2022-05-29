IN_FOLDER = '/media/brum/b2478a80-d995-4ab3-8521-e4599cc787a4/sharp_eye/cam1_new/'
OUT_FOLDER = '/media/brum/b2478a80-d995-4ab3-8521-e4599cc787a4/sharp_eye/cam1_new_x/'


import os
import cv2
import ast

FILE_LIST = []

for filename in os.listdir(IN_FOLDER):
  if filename[:2] == 'ff' and filename[-4:] == '.jpg':
    FILE_LIST.append(filename)

# Use frame number as sorting index
FILE_LIST.sort(key=lambda x: int(x.split('-')[-1][:-4]))

motion_length = 0
motion_frames = 0
prev_frame_index = 0
consecutive_motion_frames = 0

motion_array = []
current_index = 0
def iterate_frame(index):
  global motion_array
  global current_index

  while current_index < index:
    motion_array.append(False)
    current_index += 1

  motion_array.append(True)
  current_index += 1

  if len(motion_array) > 256:
    motion_array = motion_array[-256:]

for filename in FILE_LIST:
  img = cv2.imread(IN_FOLDER + filename)
  with open(IN_FOLDER + filename[:-4] + '.txt') as data_file:
    data = ast.literal_eval(data_file.read())

  frame_index = int(filename.split('-')[-1][:-4])
  motion = data['motion_detected']
  iterate_frame(frame_index)


  motion_frames = 0
  motion_length = 0
  consecutive_motion_frames = 0
  gap = 0
  for i in reversed(motion_array):
    if i:
      consecutive_motion_frames += 1
    else:
      break

  for i in reversed(motion_array):
    motion_length += 1
    if i:
      motion_frames += 1
      gap = 0
    else:
      gap += 1

    if gap >= 10:
      motion_length -= 10
      break

  prev_frame_index = frame_index

  print(filename, motion_length, motion_frames, consecutive_motion_frames, motion, motion_array[-10:])

  mark = motion_length >= 10 and motion_frames / motion_length >= 0.5

  text = '%s: ml %s, mf %s, cmf %s' % (motion, motion_length, motion_frames, consecutive_motion_frames)
  if mark:
    cv2.putText(img, "ALERT", (100, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, (0 if motion else 255, 0, 255 if motion else 0), 2)
  cv2.putText(img, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0 if motion else 255, 0, 255 if motion else 0), 2)
  cv2.rectangle(img, (data['x']*4, data['y']*4),
                     (data['x']*4 + data['w']*4, data['y']*4 + data['h']*4), (0, 255, 0), 2)
  cv2.imwrite(OUT_FOLDER + "%06d_" % frame_index + filename, img)

