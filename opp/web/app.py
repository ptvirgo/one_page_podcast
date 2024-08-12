#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flask
from uuid import UUID
import markdown2

import opp.config as config

config.init_visitor()
app = flask.Flask(__name__)


def download_extension(audio_format):
    "Produce a file extension from the given type."

    # DRY suggests that this belongs in opp.podcast, but SRP suggests that would cause unwanted interdependencies.

    if audio_format == "opus":
        return "opus"

    if audio_format == "vorbis":
        return "ogg"

    return "mp3"


def mime_type(audio_format):
    "Produce the mime type of an audio file format."

    if audio_format == "mp3":
        return "audio/mp3"

    return "audio/ogg"


def episode_url(episode):
    "Pdocuce episode url."
    return app.url_for("download_episode", guid=episode["guid"], ext=download_extension(episode["audio_format"]), _external=True)


def episode_data(episode):
    return dict(episode, url=episode_url(episode), mime_type=mime_type(episode["audio_format"]))


@app.template_filter("markdown")
def markdown(text):
    return markdown2.markdown(text)


@app.route("/")
def home():
    data = config.VISIT_PODCAST.podcast_data()
    channel = data["channel"]
    episodes = [episode_data(ep) for ep in data["episodes"]]

    return flask.render_template("podcast.html", channel=channel, episodes=episodes)


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

    result = flask.send_file(episode["path"], mimetype=mime_type(episode["audio_format"]))
    result.accept_ranges = "bytes"

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
    episodes = [episode_data(ep) for ep in data["episodes"]]

    xml = flask.render_template("podcast.xml", channel=channel, episodes=episodes)

    return flask.Response(xml, mimetype="application/rss+xml")
