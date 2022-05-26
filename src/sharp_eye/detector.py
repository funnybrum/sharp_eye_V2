import cv2
import os

from datetime import datetime

from lib.lib import log
from lib import config


class MotionDetector(object):
    """
    Motion detection.
    """

    MIN_MOTION_SIZE = (4, 8)
    NOISE_FILTERING_RECT = (2, 3)
    MOTION_THRESHOLD = config['motion']['threshold']
    MOTION_HISTORY = config['motion']['history']

    _MOTION_IMAGE_WIDTH = 480
    _MOTION_IMAGE_HEIGHT = 270

    def __init__(self, camera, on_motion):
        """
        Create motion detector.
        :param camera: camera to be used for getting snapshots
        :param on_motion: function to be called if motion is detected
        """
        if not camera or not on_motion:
            raise AssertionError('Invalid parameters')

        if 'snapshot_history' in config['motion']:
            self.snapshot_folder = os.path.join(config['motion']['snapshot_history_location'], config['identifier'])
            if not os.path.exists(self.snapshot_folder):
                os.mkdir(self.snapshot_folder)

        self.detector = cv2.createBackgroundSubtractorMOG2(history=self.MOTION_HISTORY,
                                                           varThreshold=self.MOTION_THRESHOLD,
                                                           detectShadows=True)

        self.camera = camera
        self.on_motion_callback = on_motion
        self.last_no_motion = None
        self.last_motion = None
        self.consequent_motion_frames = 0
        self.last_motion_frame = 0
        self.prev_frame = None
        self.frame_count = 0
        if 'mask' in config['motion']:
            self.mask = cv2.imread(config['motion']['mask'])
            self.mask = self.resize(self.mask)
            self.mask = cv2.cvtColor(self.mask, cv2.COLOR_BGR2GRAY)
        else:
            self.mask = None

    def resize(self, img, width=_MOTION_IMAGE_WIDTH, height=_MOTION_IMAGE_HEIGHT):
        h, w, _ = img.shape
        fx = 1.0 * width / w
        fy = 1.0 * height / h
        return cv2.resize(img, (0, 0), fx=fx, fy=fy)

    def run(self):
        """Start the motion detection loop."""

        while True:
            try:
                motion = self.check_next_frame()
            except Exception as e:
                log('Got exception: %s' % repr(e))
                motion = None

            if (motion is not False) or \
               ('debug' in config and config['debug']):
                log('Camera "%s", frame %s, motion: %s' % (config['identifier'], self.frame_count, motion))

    def _get_frame(self):
        """Get a frame from the camera and validate it. Returns the frame iff valid, None otherwise"""
        frame = self.camera.snapshot_img()
        self.frame_count += 1

        if frame is not None and self._validate_image(frame):
            return frame

    def _validate_image(self, img):
        # Check if the image is defective. We get such images where a given line is repeated till
        # the end of the image. This triggers false alarm. So we compare the last two lines of the
        # array and if they are the same - this is defective image.
        height = img.shape[0]
        result = not (img[height-2] == img[height-3]).all()
        if not result:
            log("Detected image with defect")
        return result

    def _process_frame(self, frame):
        processed_frame = self.resize(frame)
        B, G, R = cv2.split(processed_frame)

        R = cv2.equalizeHist(R)
        B = cv2.equalizeHist(B)
        G = cv2.equalizeHist(G)

        processed_frame = cv2.merge((B, G, R))
        processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2GRAY)
        # processed_frame = cv2.equalizeHist(processed_frame)

        # apply the mask that marks the motion detection region
        if self.mask is not None:
            processed_frame = cv2.bitwise_and(processed_frame, processed_frame, mask=self.mask)

        return processed_frame

    def _process_mask(self, motion_mask):
        result = {'motion_detected': False}

        # erode the motion detection mask in order to filter out the noise
        erode_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, self.NOISE_FILTERING_RECT)
        motion_mask = cv2.erode(motion_mask, erode_kernel, iterations=1)

        x, y, w, h = cv2.boundingRect(motion_mask)
        non_zero_pixels = cv2.countNonZero(motion_mask)
        if w > 0 and h > 0:
            non_zero_percent = (non_zero_pixels * 100) / (w * h)
        else:
            non_zero_percent = 0

        result.update({
            'x': x,
            'y': y,
            'w': w,
            'h': h,
            'non_zero_pixels': non_zero_pixels,
            'non_zero_percent': non_zero_percent})

        if w >= self.MIN_MOTION_SIZE[0] and h >= self.MIN_MOTION_SIZE[1]:
            # static condition, avoid sudden light changes, img size is 320 x 180
            if w > 310 and h > 170 and non_zero_percent < 7:
                pass
            elif non_zero_pixels > config['motion']['dc_pixels'] and non_zero_percent > config['motion']['dc_percent']:
                result['motion_detected'] = True
            elif non_zero_pixels > config['motion']['sc_pixels']:
                result['motion_detected'] = True

        return motion_mask, result

    def _get_frame_key(self):
        return "%s-%s" % (datetime.now().strftime("%Y-%m-%d-%H-%M"), self.frame_count)

    def _save_frame(self, frame, motion_mask, motion_info):
        if config['motion']['snapshot_history'] == 'full':
            # Write each frame on the drive
            frame_key = self._get_frame_key()
            cv2.imwrite('%s/ff_%s.jpg' % (self.snapshot_folder, frame_key), frame)
        elif config['motion']['snapshot_history'] == 'partial' and motion_info['motion_detected']:
            # Or in case of motion - save motion info on the drive
            frame_key = self._get_frame_key()
            cv2.imwrite('%s/img_%s.jpg' % (self.snapshot_folder, frame_key), motion_mask)
            cv2.imwrite('%s/ff_%s.jpg' % (self.snapshot_folder, frame_key), frame)
            ff_info = open('%s/ff_%s.txt' % (self.snapshot_folder, frame_key), 'w')
            ff_info.write(str(motion_info))
            ff_info.close

    def _get_motion_frame(self, frame, motion_mask, motion_info):
        motion_frame = self.resize(frame)
        # Draw green rect around the motion, *2 because the mask is 1/2 of the motion_frame that we are creating
        # Seems I've changed the moiton frame size, the *2 looks no-longer needed as the motion_frame is the same size
        # as the motion mask.
        x = int(motion_info['x'])
        y = int(motion_info['y'])
        w = int(motion_info['w'])
        h = int(motion_info['h'])

        cv2.rectangle(motion_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

        if 'debug' in config and config['debug']:
            # add the motion detection mask
            motion_mask = cv2.resize(motion_mask, (0, 0), fx=0.5, fy=0.5)
            motion_frame[270:360, 480:640] = cv2.cvtColor(motion_mask, cv2.COLOR_GRAY2RGB)
        return motion_frame

    def check_next_frame(self):
        """
        Check if moiton is detected. If so - calls the on_motion callback.
        :return: True iff motion is detected, False otherwise.
        """
        frame = self._get_frame()
        if frame is None:
            return 'No frame from camera'

        processed_frame = self._process_frame(frame)
        motion_mask = self.detector.apply(processed_frame)
        motion_mask, motion_info = self._process_mask(motion_mask)

        if motion_info['motion_detected']:
            self.last_motion_frame = self.frame_count

        ongoing_motion = self.frame_count - self.last_motion_frame <= config['motion']['min_no_motion_gap']

        if motion_info['motion_detected'] or ongoing_motion:
            self.consequent_motion_frames += 1
            self.on_motion_callback(motion_frame=self._get_motion_frame(frame, motion_mask, motion_info),
                                    snapshot=frame,
                                    prev_snapshot=self.prev_frame,
                                    data={'frame_count': self.frame_count,
                                          'motion_detected': motion_info['motion_detected'],
                                          'last_motion': self.last_motion,
                                          'last_no_motion': self.last_no_motion,
                                          'motion_length': self.consequent_motion_frames,
                                          'non_zero_pixels': motion_info['non_zero_pixels'],
                                          'non_zero_percent': motion_info['non_zero_percent'],
                                          'motion_rect': (motion_info['w'],
                                                          motion_info['h'])})
            self.last_motion = datetime.now()
        else:
            self.consequent_motion_frames = 0
            self.last_no_motion = datetime.now()

        self.prev_frame = frame
        self._save_frame(frame, motion_mask, motion_info)
        return motion_info['motion_detected']