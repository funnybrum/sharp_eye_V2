import os
import re

from flask import (
    send_file,
    abort,
    request,
    redirect,
    make_response,
    current_app,
    render_template,
    send_from_directory
)
from werkzeug.utils import safe_join

from lib import config
from admin import server_webapp

from admin.login import requires_auth


def get_gallery_items():
    all_movies = []
    for root, dirs, files in os.walk(config['snapshots']['location']):
        all_movies.extend([os.path.join(root, f) for f in files if f.endswith("mp4")])

    def __gen_sort_key(filename):
        # 2022-06-05-05-37-40788.mp4
        tokens = filename.replace(os.sep, "-").split("-")
        year = tokens[-6]
        month = tokens[-5]
        day = tokens[-4]
        hour = tokens[-3]
        minute = tokens[-2]
        frame_index = tokens[-1][:-4].rjust(10, "0")

        return int(year + month + day + hour + minute + frame_index)

    all_movies = sorted(all_movies, key=lambda f: __gen_sort_key(f))

    result = {}
    for movie in reversed(all_movies):
        tokens = movie.replace(os.sep, "-").split("-")
        year = tokens[-6]
        month = tokens[-5]
        day = tokens[-4]
        hour = tokens[-3]
        minute = tokens[-2]

        key = "%s-%s-%s" % (year, month, day)
        entry = {
            "path": movie[len(config['snapshots']['location'])+1:],
            "title": "%s:%s" % (hour, minute),
            "size": "{:.1f}MB".format(os.stat(movie).st_size / 1000000)
        }
        if key not in result:
            result[key] = [entry]
        else:
            result[key].append(entry)

    return result


@server_webapp.route('/gallery')
# @requires_auth
def gallery():
    data = get_gallery_items()
    return render_template('gallery.html', content=data)


@server_webapp.route("/movie/<path:filename>", methods=["GET"])
def movie(filename):
    movie_file = safe_join(config['snapshots']['location'], filename)
    return send_file(movie_file, as_attachment=True)
