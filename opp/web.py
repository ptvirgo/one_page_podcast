#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, Response, send_file
from uuid import UUID

import opp.config as config

config.init_visitor()
app = Flask(__name__)

@app.route("/episode/<guid>")
def download_episode(guid):
    """Produce the audio file for a given episode."""

    try:
        UUID(guid)
    except ValueError:
        return Response(response="Invalid episode id", status=400)

    episode = config.VISIT_PODCAST.get_episode(guid)

    if not episode:
        return Response(response="Episode not found", status=404)

    return send_file(episode["path"], mimetype=episode["audio_format"])
