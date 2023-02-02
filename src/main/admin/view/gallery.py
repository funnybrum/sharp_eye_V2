import os
import re

from flask import (
    send_file,
    request,
    render_template
)
from werkzeug.utils import safe_join

from lib import config
from admin import server_webapp

from admin.view.login import requires_auth


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
@requires_auth
def gallery():
    data = get_gallery_items()
    return render_template('gallery.html',
                           content=data,
                           session_id=request.cookies.get("session_id"),
                           prefix=request.host.replace("/gallery", ""))


@server_webapp.route("/movie/play/<path:filename>", methods=["GET"])
@requires_auth
def play_movie(filename):
    movie_file = safe_join(config['snapshots']['location'], filename)
    headers = request.headers
    if not "range" in headers:
        return send_file(movie_file)

    size = os.stat(movie_file)
    size = size.st_size

    chunk_size = 10**3
    start = int(re.sub("\D", "", headers["range"]))
    end = min(start + chunk_size, size - 1)

    content_lenght = end - start + 1

    def get_chunk(movie_file, start, end):
        with open(movie_file, "rb") as f:
            f.seek(start)
            chunk = f.read(end)
        return chunk

    headers = {
        "Content-Range": f"bytes {start}-{end}/{size}",
        "Accept-Ranges": "bytes",
        "Content-Length": content_lenght,
        "Content-Type": "video/mp4",
    }

    return server_webapp.response_class(get_chunk(movie_file, start, end), 206, headers)


@server_webapp.route("/movie/download/<path:filename>", methods=["GET"])
@requires_auth
def download_movie(filename):
    movie_file = safe_join(config['snapshots']['location'], filename)
    return send_file(movie_file, as_attachment=True)


@server_webapp.route("/movie/play_all/<path:date>", methods=["GET"])
@requires_auth
def play_all(date):
    movies = get_gallery_items()[date]
    movies = ["/movie/play/" + m["path"] for m in reversed(movies)]
    return render_template('play_all.html', movies=movies)
