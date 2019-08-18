# -*- coding: utf-8 -*-

import enum
import os
import yaml

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy


default_cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "default_settings.yml")

cfg = os.environ.get("OPP_CONFIG", default_cfg)

with open(cfg, "r") as f:
    settings = yaml.safe_load(f.read())

app = Flask(__name__)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = settings["database"]["uri"]

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
    file_name = db.Column(db.String(256), unique=True)
    audio_format = db.Column(db.Enum(AudioFormat))
    length = db.Column(db.Integer)
    duration = db.Column(db.String(8))
    episode_id = db.Column(db.Integer, db.ForeignKey("episode.item_id"))
    episode = db.relationship("Episode",
                              backref=db.backref("audio_file", uselist=False))
    # link ?

    def __repr__(self):
        return "<AudioFile %s>" % self.file_name


class Keyword(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(32))

    def __str__(self):
        return self.word

    def __repr__(self):
        return "<Keyword %s>" % self.word


@app.route("/podcast.xml")
def rss():
    episodes = Episode.query.order_by(Episode.published.desc()).all()
    return render_template("podcast.xml", site=settings["site"], episodes=episodes)
