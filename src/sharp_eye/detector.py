import cv2

from lib.lib import log
from lib import config
from sharp_eye.frame import Frame
import numpy


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

    def __init__(self, camera, event_tracker, snapshot_tracker):
        """
        Create motion detector.
        :param camera: camera to be used for getting snapshots
        :param event_tracker: event tracker object
        """
        if not camera or not event_tracker:
            raise AssertionError('Invalid parameters')

        self.detector = cv2.createBackgroundSubtractorMOG2(history=self.MOTION_HISTORY,
                                                           varThreshold=self.MOTION_THRESHOLD,
                                                           detectShadows=True)

        self.camera = camera
        self.event_tracker = event_tracker
        self.snapshot_tracker = snapshot_tracker
        self.prev_frame = None
        self.frame_count = 0
        if 'mask' in config['motion']:
            self.mask = cv2.imread(config['motion']['mask'])
            self.mask = self.resize(self.mask, interpolation=cv2.INTER_NEAREST)
            self.mask = cv2.cvtColor(self.mask, cv2.COLOR_BGR2GRAY)
            # Sanity check on the mask. It should be either one color [255] or
            # two colors [0, 255].
            mask_bytes = sorted(numpy.unique(self.mask))
            if not mask_bytes == [0, 255] and not mask_bytes == [255]:
                camera.stop()
                raise RuntimeError("Invalid mask file. Expected just 0 and 255 "
                                   "pixels, but got %s" % mask_bytes)
        else:
            self.mask = None

    def resize(self, img, width=_MOTION_IMAGE_WIDTH, height=_MOTION_IMAGE_HEIGHT, interpolation=cv2.INTER_LINEAR):
        h, w, _ = img.shape
        fx = 1.0 * width / w
        fy = 1.0 * height / h
        return cv2.resize(img, (0, 0), fx=fx, fy=fy, interpolation=interpolation)

    def run(self):
        """Start the motion detection loop."""
        try:
            while True:
                try:
                    motion = self.check_next_frame()
                except Exception as e:
                    log('Got exception: %s' % repr(e))
                    motion = None

                if motion is not False:
                    log('Camera "%s", frame %s, motion: %s' % (config['identifier'], self.frame_count, motion))
        except Exception as e:
            self.camera.stop()
            raise e

    def _get_frame(self):
        """Get a frame from the camera and validate it. Returns the frame iff valid, None otherwise"""
        frame = self.camera.snapshot_img()
        self.frame_count += 1

        if frame is not None:
            return frame

    # def _validate_image(self, img):
    #     # Check if the image is defective. We get such images where a given line is repeated till
    #     # the end of the image. This triggers false alarm. So we compare the last two lines of the
    #     # array and if they are the same - this is defective image.
    #     height = img.shape[0]
    #     result = not (img[height-2] == img[height-3]).all()
    #     if not result:
    #         log("Detected image with defect")
    #     return result

    def _process_frame(self, frame):
        processed_frame = self.resize(frame)
        B, G, R = cv2.split(processed_frame)

        R = cv2.equalizeHist(R)
        B = cv2.equalizeHist(B)
        G = cv2.equalizeHist(G)

        processed_frame = cv2.merge((B, G, R))
        processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2GRAY)

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
        # TODO - move to multiple contours
        # contours, _ = cv2.findContours(motion_mask, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)^M
        # import pdb; pdb.set_trace()^
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
            if w > 470 and h > 260 and non_zero_percent < 7:
                pass
            elif non_zero_pixels > config['motion']['dc_pixels'] and non_zero_percent > config['motion']['dc_percent']:
                result['motion_detected'] = True
            elif non_zero_pixels > config['motion']['sc_pixels']:
                result['motion_detected'] = True

        return motion_mask, result

    def check_next_frame(self):
        """
        Check if motion is detected. If so - invoke the event tracker.
        :return: True iff motion is detected, False otherwise.
        """
        frame = self._get_frame()
        if frame is None:
            return 'No frame from camera'

        processed_frame = self._process_frame(frame)
        motion_mask = self.detector.apply(processed_frame)
        motion_mask, motion_info = self._process_mask(motion_mask)

        frame_obj = Frame(
            index=self.frame_count,
            motion=motion_info['motion_detected'],
            frame=frame,
            prev_frame=self.prev_frame,
            motion_mask=motion_mask,
            non_zero_pixels=motion_info['non_zero_pixels'],
            non_zero_percent=motion_info['non_zero_percent'],
            motion_rect=(motion_info['w'], motion_info['h']),
            motion_pos=(motion_info['x'], motion_info['y'])
        )

        self.event_tracker.track_frame(frame_obj)
        self.prev_frame = frame
        return frame_obj.motion
