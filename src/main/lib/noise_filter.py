"""
Night noise filter. Recognizes motion clips that are most likely insects lit by the camera IR illuminator.

Insects near the lens show up as motion for a frame or two at random spots. Something that really moves through the
scene (a cat, a person) gives a streak of consecutive motion frames with overlapping motion areas. The check works on
the per-frame motion metadata from the .json sidecar. It is applied only to IR (black and white) videos, because it was
validated on night footage only.
"""
import cv2
import numpy

# Motion frame rule from sharp_eye/detector.py with the thresholds from camera_common.yaml. The sidecar coordinates are
# in 1920x1080, the motion detector works at 480x270.
_SCALE = 4
_MIN_MOTION_SIZE = (4, 8)
_DC_PIXELS = 10
_DC_PERCENT = 0.1
_SC_PIXELS = 40

# A clip is noise if its longest streak of consecutive motion frames is this long or shorter ...
_MAX_NOISE_RUN = 3
# ... or if the streak is shorter than this and less than half of the consecutive motion frames overlap.
_MAX_INCOHERENT_RUN = 5
_MIN_COHERENCE = 0.5


def _is_motion_frame(frame_metadata):
    motion = frame_metadata['motion']
    w = motion['w'] / _SCALE
    h = motion['h'] / _SCALE
    pixels = frame_metadata['non_zero_pixels']
    percent = frame_metadata['non_zero_percent']
    if w < _MIN_MOTION_SIZE[0] or h < _MIN_MOTION_SIZE[1]:
        return False
    if w > 470 and h > 260 and percent < 7:
        # Sudden light change over the whole image.
        return False
    return (pixels > _DC_PIXELS and percent > _DC_PERCENT) or pixels > _SC_PIXELS


def _overlap(motion_a, motion_b):
    """Check if two motion areas overlap after growing each by 25% of its size on every side."""
    def grow(m):
        return (m['x'] - m['w'] * 0.25, m['y'] - m['h'] * 0.25,
                m['x'] + m['w'] * 1.25, m['y'] + m['h'] * 1.25)
    a = grow(motion_a)
    b = grow(motion_b)
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def is_night_noise(video_file, motion_metadata):
    """
    Check if a motion clip is night noise: insect like motion in an IR video.
    :param video_file: the motion video
    :param motion_metadata: the parsed .json sidecar, one item per frame
    :return: True if the clip is night noise. False without motion metadata: the sidecar is written after the video is
    complete, so without it the video may still be encoded.
    """
    if not motion_metadata:
        return False
    return _is_insect_motion(motion_metadata) and _is_ir_video(video_file)


def _is_insect_motion(motion_metadata):
    """
    Check if the motion in a clip looks like insects.
    :param motion_metadata: the parsed .json sidecar, one item per frame
    :return: True if the clip is noise, False otherwise (also if the metadata can't be interpreted)
    """
    try:
        motion_flags = [_is_motion_frame(f) for f in motion_metadata]
    except (KeyError, TypeError):
        return False

    longest_run = run = pairs = overlapping = 0
    for i, is_motion in enumerate(motion_flags):
        if not is_motion:
            run = 0
            continue
        run += 1
        longest_run = max(longest_run, run)
        if i > 0 and motion_flags[i - 1]:
            pairs += 1
            if _overlap(motion_metadata[i - 1]['motion'], motion_metadata[i]['motion']):
                overlapping += 1

    if longest_run <= _MAX_NOISE_RUN:
        return True
    return longest_run <= _MAX_INCOHERENT_RUN and pairs > 0 and overlapping / pairs < _MIN_COHERENCE


def _is_ir_video(video_file):
    """Check if the camera was in IR (black and white) mode, based on the first video frame having no colour."""
    # Single decoder thread. With the default (one per core) FFmpeg decodes several frames ahead and that costs about
    # 8x more CPU for the one frame needed here.
    capture = cv2.VideoCapture(video_file, cv2.CAP_FFMPEG, [cv2.CAP_PROP_N_THREADS, 1])
    ret, frame = capture.read()
    capture.release()
    if not ret:
        return False

    # Skip the text stamp at the top of the frame, it may be coloured.
    small = cv2.resize(frame, (480, 270))[20:]
    ycrcb = cv2.cvtColor(small, cv2.COLOR_BGR2YCrCb).astype(numpy.int16)
    colour = numpy.abs(ycrcb[:, :, 1] - 128) + numpy.abs(ycrcb[:, :, 2] - 128)
    return (colour > 6).mean() < 0.01
