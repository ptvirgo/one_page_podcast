#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flask
from uuid import UUID

import opp.config as config

config.init_visitor()
app = flask.Flask(__name__)


def download_extension(audio_mimetype):
    "Produce a file extension from the given mime type."

    # DRY suggests that this belongs in opp.podcast, but SRP suggests that would cause unwanted interdependencies.

    if audio_mimetype == "audio/ogg":
        return "opus"  # not a typo

    if audio_mimetype == "audio/vorbis":
        return "ogg"

    return "mp3"


@app.route("/episode/<guid>.<ext>", methods=["GET", "HEAD"])
def download_episode(guid, ext="mp3"):
    """Produce the audio file for a given episode."""

    try:
        UUID(guid)
    except ValueError:
        return flask.Response(response="Invalid episode id", status=400)

    episode = config.VISIT_PODCAST.get_episode(guid)

    if not episode:
        return flask.Response(response="Episode not found", status=404)

    result = flask.send_file(episode["path"], mimetype=episode["audio_format"])

    if flask.request.method == "HEAD" or flask.request.method == "GET":
        return result

    return flask.Response(response="Invalid request", status=400)


@app.route("/image")
def podcast_image():
    """Produce the podcast image, if available."""

    data = config.VISIT_PODCAST.podcast_data()
    image = data["channel"]["image"]

    if image is None:
        return flask.Response(response="Not found", status=404)

    return flask.send_file(image)


@app.route("/rss.xml")
def rss():
    data = config.VISIT_PODCAST.podcast_data()

    channel = data["channel"]
    episodes = data["episodes"]

    for ep in episodes:
        ep["url"] = app.url_for("download_episode", guid=ep["guid"], ext=download_extension(ep["audio_format"]), _external=True)

    xml = flask.render_template("podcast.xml", channel=channel, episodes=episodes)

    return flask.Response(xml, mimetype="application/rss+xml")
