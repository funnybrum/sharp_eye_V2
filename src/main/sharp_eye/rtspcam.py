import cv2
import numpy
import os
import re
import shutil
import time


from io import BytesIO
from subprocess import Popen

from lib import config

from lib.lib import (
    log,
    get_process_name,
    is_running,
    kill,
    kill_all
)
from lib.quicklock import attach_sub_process


class RtspCamera(object):
    """
    An interface for getting snapshots from a video stream.

    Uses ffmpeg as subprocess to extract frames from the video stream on regular intervals ("-r 1" sets the frame rate).
    The process is being monitored and will be restarted if it dies.
    """

    STREAMING_COMMAND = "/usr/bin/ffmpeg -hwaccel vaapi -nostats -loglevel 0 -rtsp_transport tcp -i %s -y -r 2 %s/_%s_%%d.bmp"

    def __init__(self):
        """
        Initialize the video streaming camera object.

        This step also starts the ffmpeg subprocess. An exception is raised if this fails.
        """

        self.streaming_command = self.STREAMING_COMMAND % (
            config[config['identifier']]['stream_uri'],
            config['tmp_folder'],
            config['identifier']
        )

        self.tmp_file_re = re.compile(self.streaming_command
                                      .split(' ')[-1]
                                      .replace('%d.', '.*')
                                      .replace(config['tmp_folder'] + "/", ""))
        self.streaming_process_name = None
        self.streaming_process_pid = None
        self._start_streaming()

    def _clean_temp_files(self):
        files = os.listdir(config['tmp_folder'])
        files = [config['tmp_folder'] + "/" + f for f in files if self.tmp_file_re.match(str(f))]
        for f in files:
            os.remove(f)

    def _start_streaming(self):
        log("Streaming process - clean up")
        kill_all([self.streaming_command])

        log("Streaming process - starting")
        try:
            self._clean_temp_files()

            DEVNULL = open(os.devnull, 'wb')
            self.streaming_process_pid = Popen(self.streaming_command.split(' '), stdin=DEVNULL).pid
            self.streaming_process_name = get_process_name(self.streaming_process_pid)

            attach_sub_process(self.streaming_process_pid)
            log("Streaming process - started")

            # Wait till a new file is generated
            timeout = 20  # 20 seconds timeout for he process startup
            while not self._get_oldest_snapshot() and timeout > 0:
                time.sleep(0.05)
                timeout -= 0.05

            if timeout <= 0:
                raise RuntimeError("Timeout while waiting for streaming process to start")

            log("Streaming process - verified")
        except Exception as e:
            log('Failed to run RTSP client: %s' % repr(e))

    def _kill_streaming(self):
        log("Streaming process - killing")
        kill(self.streaming_process_pid)
        self.streaming_process_pid = None

    def _restart_streaming(self):
        self._kill_streaming()
        self._start_streaming()

    def _verify_streaming(self, force_restart=False):
        """
        Check if the background streaming process is running and if not - start it.
        :param force_restart: if True - kill the old streaming process and start new one.
        """
        running = is_running(self.streaming_process_pid, self.streaming_process_name)
        if not running or force_restart:
            self._restart_streaming()

    def _get_oldest_snapshot(self):
        files = os.listdir(config['tmp_folder'])
        files = [f for f in files if self.tmp_file_re.match(str(f))]
        files = sorted(files, key=lambda f: int(f.split("_")[-1][:-4]))

        if files and len(files) > 1:
            return config['tmp_folder'] + '/' + files[0]

    def _get_snapshot(self, timeout):
        """
        Get snapshot from the camera.
        :param retries: how many retries to be done for getting the snapshot
        :param retry_delay: delay (sec) between retries
        :return: BytesIO
        """
        self._verify_streaming()

        # Wait for a new file to pop up
        oldest_snapshot = None
        while not oldest_snapshot and timeout > 0:
            oldest_snapshot = self._get_oldest_snapshot()
            time.sleep(0.05)
            timeout -= 0.05

        if not oldest_snapshot:
            self._restart_streaming()
            return None

        with open(oldest_snapshot, 'rb') as img_input:
            result = BytesIO(img_input.read())

        shutil.copy(oldest_snapshot, config[config['identifier']]['snapshot'])
        os.remove(oldest_snapshot)
        return result

    def snapshot_img(self, timeout=config['motion']['snapshot_timeout']):
        """
        Get snapshot from the camera.
        :param timeout: timeout for attempting to retrieve an image
        :return: cv2 image object representing the snapshot
        """
        start = time.time()
        img_fd = self._get_snapshot(timeout=timeout)
        if not img_fd:
            log("Time: %s, FAIL" % round(time.time() - start, 2))
            return None
        # log("Time: %s, OK, %s" % (round(time.time() - start, 2), len(img_fd.getvalue())))
        img_array = numpy.fromstring(img_fd.getvalue(), dtype=numpy.uint8)
        result = cv2.imdecode(img_array, flags=cv2.IMREAD_UNCHANGED)
        return result

    def stop(self):
        self._kill_streaming()
        self._clean_temp_files()
