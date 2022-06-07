import cv2
import os
import shutil
import threading
import time

from datetime import datetime
from subprocess import Popen

from lib import config

from lib.log import log


class SnapshotTracker(object):
    def __init__(self):
        self._frames = {}
        self._history_length = config['snapshots']['history']
        self._snapshot_folder = os.path.join(config['tmp_folder'], config['identifier'])
        if not os.path.exists(self._snapshot_folder):
            os.mkdir(self._snapshot_folder)
        self._video_folder = os.path.join(config['snapshots']['location'], config['identifier'])
        if not os.path.exists(self._video_folder):
            os.mkdir(self._video_folder)
        self._snapshot_files = []

    def process_frame(self, frame):
        self._frames[frame.index] = frame

        while len(self._frames) > self._history_length:
            self._frames.pop(next(iter(self._frames)))

        if config['snapshots']['type'] != 'full':
            return

        self._save_frame(frame.index)

    def on_single_motion_frame(self):
        if config['snapshots']['type'] != 'motion_frame':
            return

        index = self._frames.keys()[-1]
        self._save_frame(index)

    def on_sequence_motion_frame(self):
        if config['snapshots']['type'] != 'motion_sequence':
            return

        for index in iter(self._frames):
            self._snapshot_files.append(self._save_frame(index))

        if len(self._snapshot_files) >= 120:
            self._create_motion_video(True)
            self._snapshot_files = []

        self._frames = {}

    def on_sequence_end(self):
        self._create_motion_video(False)
        self._snapshot_files = []

    def _save_frame(self, frame_index):
        """
        Persist a frame on the tmp file system. This will likely (depending on the config)
        be used to create a motion video file later on.
        """
        frame_key = "%s-%s" % (datetime.now().strftime("%Y-%m-%d-%H-%M"), frame_index)
        frame = self._frames[frame_index]
        snapshot_filename = '%s/%s.bmp' % (self._snapshot_folder, frame_key)
        cv2.imwrite(snapshot_filename, frame.get_motion_frame())
        return snapshot_filename

    def _create_motion_video(self, partial):
        video_out_file = os.path.join(
            self._video_folder,
            os.path.split(self._snapshot_files[0])[-1][:-3] + "mp4"
        )

        compression_thread = threading.Thread(
            target=self._compression_thread,
            args=(video_out_file, self._snapshot_files, partial))
        compression_thread.start()

    @staticmethod
    def _compression_thread(output_file, in_files, partial):
        video_in_txt_file = output_file[:-3] + "txt"
        if partial:
            frame_files = in_files
        else:
            frame_files = in_files[:-int(0.9 * config['event_tracker']['min_no_motion_gap'])]

        if len(frame_files) > 0:
            # Prepare list of images to be converted to a video file
            with open(video_in_txt_file, 'w') as out:
                out.write("ffconcat version 1.0\n")
                for f in frame_files:
                    out.write("file '%s'\nduration 0.1\n" % f)

            # Determine the usage of the temporary file system. If usage is high go with low quality
            # video to speed up the process of reducing the usage. High usage will render the system
            # non-working because there will be no space to store camera snapshots for processing.
            total, used, _ = shutil.disk_usage('/tmp')
            # Determine the current load. 0 is low load, 10 is highest possible.
            load = int(10 * used / total)
            preset_map = [
                'medium',
                'medium',
                'medium',
                'fast',
                'fast',
                'faster',
                'veryfast',
                'superfast',
                'ultrafast',
                'ultrafast',
                'ultrafast'
            ]
            ffmpeg_preset = preset_map[load]

            # Create a video file using ffmpeg.
            # 10 fps, no console output, x265, crf 25 (default is 23), slow preset (default is slow).
            # Check https://trac.ffmpeg.org/wiki/Encode/H.264 and https://trac.ffmpeg.org/wiki/Encode/H.265
            cmd = "nice -n %d /usr/bin/ffmpeg -nostats -loglevel 0 -y -safe 0 " \
                  "-r 10 -i %s " \
                  "-c:v libx265 -preset %s -crf 25 %s" % \
                  (8 - load, video_in_txt_file, ffmpeg_preset, output_file)

            log("Creating motion video %s with %s preset at nice level %d" %
                (os.path.split(output_file)[-1]), ffmpeg_preset, 8 - load)
            start_time = time.time()
            dev_null = open(os.devnull, 'wb')
            Popen(cmd.split(' '), stdin=dev_null, stdout=dev_null, stderr=dev_null).wait()

            log("Motion video %s created in %.1ds with %d frames" % (
                os.path.split(output_file)[-1],
                time.time() - start_time,
                len(frame_files)
            ))

            os.remove(video_in_txt_file)

        # Remove the snapshots that were persisted for creating the motion video.
        for f in in_files:
            os.remove(f)
