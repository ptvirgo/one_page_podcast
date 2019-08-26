# -*- coding: utf-8 -*-

from copy import deepcopy
from datetime import datetime
import enum
import markdown
import os
import pytz
import yaml

from flask import Flask, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy


# Configuration

DEFAULT_CFG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "default_settings.yml")

CFG = os.environ.get("OPP_CONFIG", DEFAULT_CFG)

with open(CFG, "r") as f:
    SETTINGS = yaml.safe_load(f.read())

app = Flask(__name__,
            template_folder=SETTINGS["configuration"]["directories"]["template"],
            static_folder=SETTINGS["configuration"]["directories"]["static"])

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = SETTINGS["configuration"]["database_uri"]


# Template formatters

def format_datetime(dt, fmt="ymd"):
    """
    Format a date time object for the jinja templates
    """
    formats = {
        "ymd": "%Y-%m-%d",
        "rfc822": "%a, %d %b %Y %H:%M:%S %z"}
    dt = pytz.timezone("utc").localize(dt)
    local = pytz.timezone(SETTINGS["configuration"]["timezone"])
    return dt.astimezone(local).strftime(formats[fmt])


def format_episode_keywords(kws):
    """
    Convert a list of Keyword objects to a comma separated string of the words
    """
    return ",".join([kw.word for kw in kws])


def format_duration(time):
    """Format an AudioFile duration"""
    hours = time // (60 * 60)
    minutes = (time - (hours * 60 * 60)) // 60
    seconds = (time - (hours * 60 * 60)) - (minutes * 60)

    if hours > 0:
        return "%02d:%02d:%02d" % (hours, minutes, seconds)

    if minutes > 0:
        return "%02d:%02d" % (minutes, seconds)

    return "%02d" % seconds


app.jinja_env.filters["datetime"] = format_datetime
app.jinja_env.filters["episode_keywords"] = format_episode_keywords
app.jinja_env.filters["duration"] = format_duration
app.jinja_env.filters["markdown"] = markdown.markdown

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
    MP3 = "audio/mpeg"
    OggVorbis = "audio/ogg"
    OggOpus = "audio/ogg"  # not a typo


class AudioFile(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(256), unique=True, index=True)
    audio_format = db.Column(db.Enum(AudioFormat))
    length = db.Column(db.Integer)
    duration = db.Column(db.Integer)
    episode_id = db.Column(
        db.Integer, db.ForeignKey("episode.item_id", ondelete="CASCADE"))
    episode = db.relationship("Episode", backref=db.backref(
        "audio_file", uselist=False, cascade="all, delete-orphan"))

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

@app.route("/")
def home():
    """
    Produce the main page
    """
    episodes = Episode.query.order_by(Episode.published.desc()).filter(
        Episode.published < datetime.utcnow())
    podcast = deepcopy(SETTINGS["podcast"])

    return render_template("index.html", podcast=podcast, episodes=episodes)


@app.route("/podcast.xml")
def rss():
    """
    Produce the podcast xml
    """
    episodes = Episode.query.order_by(Episode.published.desc()).filter(
        Episode.published < datetime.utcnow())
    podcast = deepcopy(SETTINGS["podcast"])

    if episodes.count() > 0:
        podcast["published"] = episodes[0].published
    else:
        podcast["published"] = datetime.utcnow()

    return render_template("podcast.xml", podcast=podcast, episodes=episodes,
                           mimetype="application/rss+xml")


@app.route("/media/<path:filename>")
def media(filename):
    return send_from_directory(
        SETTINGS["configuration"]["directories"]["media"],
        filename, as_attachment=False)
