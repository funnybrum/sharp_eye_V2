import datetime
import inspect
import os
import sys

from lib import config


def log(message, debug=False, process=config.get('identifier')):
    """
    Log message to stdout with time prefix.

    :param message: log message
    :param debug: if set to true the message will be logged only if env property DEBUG is set to 'true'

    """
    if debug and os.getenv("DEBUG", "false").lower() != "true":
        return

    frame = inspect.stack()[1]
    filename = frame[0].f_code.co_filename
    filename = os.path.basename(filename).replace('.py', '')

    timestamp = datetime.datetime.now().strftime('[%d/%m/%y %H:%M:%S]')
    print('[%s][%s]%s %s' % (process, filename, timestamp, message))
    sys.stdout.flush()
