import os
import re
import json
import time

from lib import config
from lib.lib import (
    log,
    get_process_name,
    is_running,
    kill
)


def _get_lock_file(resource, dir_name):
    lock_root = os.path.realpath(dir_name)

    if not os.path.exists(lock_root):
        os.mkdir(lock_root)

    lock_name = re.sub(r'[^a-zA-Z0-9]+', '_', resource)
    return os.path.join(lock_root, lock_name + '.lock')


def _load_lock_data(lock_file):
    if os.path.exists(lock_file):
        with open(lock_file, 'r') as lock_handle:
            return json.load(lock_handle)


def _save_lock_data(lock_file, lock_data):
    with open(lock_file, 'w') as lock_handle:
        json.dump(lock_data, lock_handle)


def _check_lock(lock_file):
    """
    Check if the lock is active. If so - return the PID of the process that has locked the
    resource. If the lock is not valid - return None.

    :param resource: Name of the resource to lock.
    :param dir_name: Base directory to store lock files.
    :return: PID of the process holding the lock iff the lock is active, None otherwise.
    """

    # Check if the process that locked the file is still running
    try:
        if os.path.exists(lock_file):
            with open(lock_file, 'r') as lock_handle:
                data = json.load(lock_handle)

            if is_running(data['pid'], data['name']):
                return data['pid']
    except Exception as exc:
        log('Unexpected exception, unlocking: %s' % repr(exc))

    return None


def is_locked(resource, dir_name=config['tmp_folder']):
    """
    Check if certain resource is locked.

    :param resource: the resource ID
    :param dir_name: folder used for storing resource lock files
    :return:
    """
    lock_file = _get_lock_file(resource, dir_name)
    return _check_lock(lock_file) is not None


def lock(resource=config['identifier'], dir_name=config['tmp_folder']):
    """
    Lock a resource. If the resource is already locked raises RuntimeError.

    :param resource: resource ID to lock
    :param dir_name: folder used for storing resource lock files
    """
    # Check if the process that locked the file is still running 
    lock_file = _get_lock_file(resource, dir_name)
    locked_by_pid = _check_lock(lock_file)
    if locked_by_pid:
        raise RuntimeError('Resource %s is locked by PID %s' % (resource, locked_by_pid))

    # Create the lock with the current process information
    pid = os.getpid()
    process_name = get_process_name(pid)
    _save_lock_data(lock_file,
                    {
                        "name": process_name,
                        "pid": pid,
                        "timestamp": int(time.time()),
                        "sub_processes": []
                    })


def attach_sub_process(pid, resource=config['identifier'], dir_name=config['tmp_folder']):
    """
    Attach sub-processes to the current lock.

    Attached sub-processes are considered as part of the process. If the main process is killed by invoking force_unlock
    all sub-processes are also killed.

    :param pid: PID of the subprocess to be attached to the lock
    :param resource: resource ID to lock
    :param dir_name: folder used for storing resource lock files
    """
    if not is_running(pid):
        return

    # Check if the lock is still valid.
    lock_file = _get_lock_file(resource, dir_name)
    locked_by_pid = _check_lock(lock_file)
    if os.getpid() != locked_by_pid:
        raise RuntimeError('Invalid lock detected')

    data = _load_lock_data(lock_file)

    # Collect attached sub-processes and filter out these that are already dead.
    sub_processes = []
    for process in data["sub_processes"]:
        if is_running(process["pid"], process["process_name"]):
            sub_processes.append(process)

    # Add the new sub-process to the list.
    sub_processes.append({
        "pid": pid,
        "process_name": get_process_name(pid)
    })

    # Update the list of sub-processes attached to the lock.
    data["sub_processes"] = sub_processes

    _save_lock_data(lock_file, data)


def force_unlock(resource, dir_name=config['tmp_folder']):
    """
    Unlock a resource. Or shortly - kill the process that has locked the resource.

    :param resource: Name of the resource to lock
    :param dir_name: Base directory to store lock files, default is /var/tmp
    """
    lock_file = _get_lock_file(resource, dir_name)
    pid = _check_lock(lock_file)
    data = _load_lock_data(lock_file)

    if pid:
        kill(pid)

    for subproc in data["sub_processes"]:
        if is_running(subproc["pid"], subproc["process_name"]):
            kill(subproc["pid"])

