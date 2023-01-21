import cv2

from lib import config


class Frame:
    def __init__(self,
                 index,
                 motion,
                 frame,
                 prev_frame,
                 motion_mask,
                 non_zero_pixels,
                 non_zero_percent,
                 motion_pos,
                 motion_rect):
        self.index = index
        self.motion = motion
        self.frame = frame
        self.prev_frame = prev_frame
        self.motion_mask = motion_mask
        self.non_zero_pixels = non_zero_pixels
        self.non_zero_percent = non_zero_percent
        self.motion_pos = motion_pos
        self.motion_rect = motion_rect

    def get_metadata(self):
        return {
            'index': self.index,
            'motion': self.motion,
            'non_zero_pixels': self.non_zero_pixels,
            'non_zero_percent': self.non_zero_percent,
            'motion_rect': self.motion_rect
        }

    def get_motion_frame(self, scale=1):
        motion_frame = self.frame.copy()
        x, y = self.motion_pos
        w, h = self.motion_rect

        cv2.resize(motion_frame, (0, 0), fx=scale, fy=scale)
        # * 4 comes from _MOTION_IMAGE_WIDTH and _MOTION_IMAGE_HEIGHT. The
        # images are at resolution 1920 x 1080 and motion is being detected
        # at 4 times lower resolution.
        x = int(x * scale * 4)
        y = int(y * scale * 4)
        w = int(w * scale * 4)
        h = int(h * scale * 4)

        cv2.rectangle(motion_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

        stamp = "{:d} / {:.2f} / {} / {}".format(self.non_zero_pixels, self.non_zero_percent, self.motion, self.index)
        pixel = self.frame[0][0]

        if pixel[0] == pixel[1] == pixel[2]:
            # black and white image, green text is easily visible
            color = (128, 255, 128)
        else:
            color = (config['snapshot']['text'][0], config['snapshot']['text'][1], config['snapshot']['text'][2])

        cv2.putText(motion_frame, stamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        return motion_frame
