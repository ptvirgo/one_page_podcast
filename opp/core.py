# -*- coding: utf-8 -*-

import pytz
from copy import deepcopy
import enum
import os
import yaml

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy


# Configuration

DEFAULT_CFG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "default_settings.yml")

CFG = os.environ.get("OPP_CONFIG", DEFAULT_CFG)

with open(CFG, "r") as f:
    SETTINGS = yaml.safe_load(f.read())

app = Flask(__name__)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = SETTINGS["configuration"]["database_uri"]


# Template formatters

def format_datetime(dt, fmt="ymd"):
    """
    Format a date time object for the jinja templates
    """
    formats = {
        "ymd": "%Y-%m-%d",
        "rfc822": "%a, %d %b %Y %H:%M:%S %z"
    }
    dt = pytz.timezone("utc").localize(dt)
    local = pytz.timezone(SETTINGS["configuration"]["timezone"])
    return dt.astimezone(local).strftime(formats[fmt])


def format_episode_keywords(kws):
    return ",".join([kw.word for kw in kws])


app.jinja_env.filters["datetime"] = format_datetime
app.jinja_env.filters['episode_keywords'] = format_episode_keywords

# Database tables

db = SQLAlchemy(app)
episode_keywords = db.Table(
    "episode_keywords",
    db.Column("episode_id", db.Integer, db.ForeignKey("episode.item_id"),
              primary_key=True),
    db.Column("keyword_id", db.Integer, db.ForeignKey("keyword.item_id"),
              primary_key=True))


class Episode(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    published = db.Column(db.DateTime, nullable=False, index=True)
    description = db.Column(db.String(4096), nullable=False)
    image = db.Column(db.String(256))
    explicit = db.Column(db.Boolean, default=False, nullable=False)

    keywords = db.relationship("Keyword", backref="episodes",
                               secondary=episode_keywords)

    def __repr__(self):
        return "<Episode %s, %s>" % (self.published.isoformat(), self.title)


class AudioFormat(enum.Enum):
    mp3 = "audio/mpeg"
    mp4 = "audio/mp4"
    ogg = "audio/ogg"
    opus = "audio/opus"


class AudioFile(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(256), unique=True, index=True)
    audio_format = db.Column(db.Enum(AudioFormat))
    length = db.Column(db.Integer)
    duration = db.Column(db.String(8))
    episode_id = db.Column(db.Integer, db.ForeignKey("episode.item_id"))
    episode = db.relationship("Episode",
                              backref=db.backref("audio_file", uselist=False))

    def __repr__(self):
        return "<AudioFile %s>" % self.file_name


class Keyword(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(32))

    def __str__(self):
        return self.word

    def __repr__(self):
        return "<Keyword %s>" % self.word


# Web routes

@app.route("/podcast.xml")
def rss():
    episodes = Episode.query.order_by(Episode.published.desc()).all()
    podcast = deepcopy(SETTINGS["podcast"])

    if len(episodes) > 0:
        podcast["published"] = episodes[0].published

    return render_template("podcast.xml", podcast=podcast, episodes=episodes)
