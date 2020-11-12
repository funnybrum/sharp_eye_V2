from __future__ import absolute_import

import os
from lib.log import log


def _run_command(command, debug=os.getenv('DEBUG', "False").lower() == "true"):
    """ Run command and return its output. """
    log("Executing command \"%s\"" % command, debug=True)
    process = os.popen(command)
    output = process.read()
    process.close()
    log("Command result: %s" % output, debug=True)
    return output


def kill(pid):
    """ kill the specified PID """
    _run_command("/bin/kill %s" % pid)


def kill_all(cmd_substrings):
    """
    Kill all processes that contain the specified substrings in the command.

    I.e. kill_all(['ffmpeg', '/tmp/cam1.png') will kill all process that contain in the commands used to start them the
    'ffmpeg' and '/tmp/cam1.png' strings.

    :param cmd_substrings: List of sub-strings that should be contained int the process command.
    :return:
    """
    # Generate the command, i.e.
    # kill $(ps auxww | grep  -F 'ffmpeg' | grep  -F 'cam1.png' | awk '{print $2}')
    cmd = "kill $(ps auxww "
    for cmd_substring in cmd_substrings:
        cmd += "| grep -F '%s' " % cmd_substring
    cmd += "| awk '{print $2}')"
    _run_command(cmd)


def get_process_name(pid):
    return _run_command('ps -p %s -o comm=' % pid).rstrip()


def is_running(pid, process_name=None):
    """
    Check if the specified process is running.

    If process name is specified a further validation is performed to confirm that the specified process name matches
    the actual process name.

    :param pid: the process ID
    :param process_name: the expected process name
    :return: True iff the process is running
    """
    return os.path.exists('/proc/%s' % pid) and (process_name is None or process_name == get_process_name(pid))
