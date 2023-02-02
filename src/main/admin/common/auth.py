import hashlib

from time import time
from functools import wraps

from flask import (
    request,
    make_response,
    redirect,
    abort
)

from lib import config
from admin import scheduler

_valid_sessions = {}


def is_valid_session_id(session_id):
    session_metadata = _valid_sessions.get(session_id)
    if not session_metadata:
        return False

    if session_metadata["expiry"] < time():
        return False

    return True


def remove_session_id(session_id):
    if session_id in _valid_sessions:
        del _valid_sessions[session_id]


def get_session_user(session_id):
    if is_valid_session_id(session_id):
        return _valid_sessions[session_id]["user"]


def validate_user(user, password):
    """
    Validate user and password. If valid - generate session id, store it
    and return it. If not - returns None.
    """
    user_id = None
    for user_data in config["credentials"]["users"]:
        if user_data["name"] == user and password == user_data["password"]:
            user_id = user
            break

    if not user_id:
        return None

    session_id = hashlib\
        .sha256(bytes(user, encoding="utf-8") + bytes(str(time()), encoding="utf-8"))\
        .hexdigest()

    _valid_sessions[session_id] = {
        "expiry": int(time()) + config["credentials"]["session_expiry"],
        "user": user
    }
    return session_id


def requires_auth(f):
    """Wrapper for routes that requires auth."""
    @wraps(f)
    def decorated(*args, **kwargs):
        from admin.common.auth import is_valid_session_id
        if is_valid_session_id(request.cookies.get("session_id")):
            return f(*args, **kwargs)

        if "session_id" in request.args and is_valid_session_id(request.args["session_id"]):
            return f(*args, **kwargs)

        if "user" in request.args and "password" in request.args:
            session_id = validate_user(request.args["user"], request.args["password"])
            if session_id:
                response = make_response(redirect(request.path))
                response.set_cookie("session_id", value=session_id)
                return response

        return redirect("/login")
    return decorated


def requires_service_auth(f):
    """Wrapper for routes that require service auth."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_cookie_token = request.cookies.get("auth_token")
        auth_arg_token = request.args.get("auth_token")
        if auth_cookie_token and auth_cookie_token in config['credentials']['services']:
            return f(*args, **kwargs)
        if auth_arg_token and auth_arg_token in config['credentials']['services']:
            return f(*args, **kwargs)
        return abort(401)
    return decorated


@scheduler.task('cron', id='session_cleanup', minute='30')
def session_cleanup():
    to_be_deleted = [s for s in _valid_sessions if s["expiry"] < time()]
    for session in to_be_deleted:
        del _valid_sessions[session]
