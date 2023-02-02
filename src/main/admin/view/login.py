from flask import (
    request,
    redirect,
    make_response,
    render_template
)

from admin import server_webapp
from admin.common.auth import (
    validate_user,
    remove_session_id,
    requires_auth
)


@server_webapp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        user = str(request.form["user"])
        password = str(request.form["password"])
        session_id = validate_user(user, password)
        if session_id:
            response = make_response(redirect("/"))
            response.set_cookie("session_id", value=session_id)
            return response

        return redirect("/login")


@server_webapp.route("/logout")
@requires_auth
def logout():
    session_id = request.cookies.get("session_id")
    remove_session_id(session_id)
    return redirect("/")