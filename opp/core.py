# -*- coding: utf-8 -*-

from cleantext import clean
from copy import deepcopy
from datetime import datetime
import enum
import markdown
import mutagen
import os
import io
import pytz
import yaml

from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from flask_jwt_simple import JWTManager, jwt_required, create_jwt, \
     get_jwt_identity
from flask_sqlalchemy import SQLAlchemy

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

import wtforms as form
from wtforms.ext.dateutil.fields import DateTimeField
import wtforms.validators as validator

from .helpers import audio_file_name, random_text

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
app.config["SECRET_KEY"] = random_text(32)
app.config["JWT_SECRET_KEY"] = random_text(32)
app.config["WTF_CSRF_ENABLED"] = False

JWT = JWTManager(app)


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
    MP3 = "mp3"
    OggOpus = "opus"
    OggVorbis = "ogg"

    @property
    def mimetype(self):
        """Produce the mime-type for this audio format"""
        kvp = {
            AudioFormat.MP3: "audio/mpeg",
            AudioFormat.OggOpus: "audio/ogg",  # not a typo
            AudioFormat.OggVorbis: "audio/ogg"}

        return kvp[self]


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

# - Front end for users

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

    content = render_template("podcast.xml", podcast=podcast,
                              episodes=episodes)
    return Response(content, content_type="application/rss+xml")


@app.route("/media/<path:filename>")
def media(filename):
    return send_from_directory(
        SETTINGS["configuration"]["directories"]["media"],
        filename, as_attachment=False)


# - Administrative

@app.route("/admin/login", methods=["POST"])
def login():
    """
    Allow site administrator to log in
    """
    if not request.is_json:
        return jsonify({"msg": "Invalid JSON"}), 400

    params = request.get_json()
    username = params.get("username")
    password = params.get("password")

    if username is None or password is None:
        return jsonify({"msg": "Missing credentials"}), 400

    if username != SETTINGS["configuration"]["admin"]["username"] \
            or password != SETTINGS["configuration"]["admin"]["password"]:
        return jsonify({"msg": "Invalid credentials"}), 401

    return jsonify({"jwt": create_jwt(identity=username)}), 200


class CreateEpisodeForm(FlaskForm):
    """
    Provide a form for creating episodes
    """
    title = form.StringField(
        label="Title", validators=[validator.DataRequired()])
    published = DateTimeField(
        label="Publication date & time", validators=[validator.DataRequired()])
    description = form.StringField(
        label="Description", validators=[validator.DataRequired()])
    explicit = form.BooleanField(label="Explicit")
    keywords = form.StringField(
        label="Keywords", validators=[validator.Optional()])
    audio_file = FileField(
        label="Audio file", validators=[FileRequired()])


@app.route("/admin/episode/new", methods=["GET", "POST"])
def episode_create():
    """
    Allow administrator to create new episodes
    """
    if request.method == "GET":
        raise NotImplementedError("Hang on!")

    form = CreateEpisodeForm()

    if form.validate_on_submit():
        af_data = form.audio_file.data.read()
        af = mutagen.File(io.BytesIO(af_data))

        try:
            af_format = AudioFormat[af.__class__.__name__]
        except KeyError:
            msg = "Invalid audio format"
            app.logger.warning(msg)
            return jsonify({"error": msg}), 400

        af_name = audio_file_name(
            form.published.data, form.title.data, af_format)

        af_path = os.path.join(
            SETTINGS["configuration"]["directories"]["media"], af_name)

        with open(af_path, "wb") as f:
            f.write(af_data)
            app.logger.info("Saved %s" % af_path)

        episode = Episode(
            title=form.title.data,
            published=form.published.data,
            description=form.description.data,
            explicit=form.explicit.data)

        audio_file = AudioFile(
            file_name=af_name,
            audio_format=af_format,
            length=os.path.getsize(af_path),
            duration=round(af.info.length))

        episode.audio_file = audio_file

        if form.keywords.data is not None:
            for word in form.keywords.data.split(","):
                word = clean(word)
                kw = Keyword.query.filter_by(word=word).first()

                if kw is None:
                    kw = Keyword(word=word)

                episode.keywords.append(kw)

        db.session.add(episode)
        db.session.commit()

        return jsonify({"success": True}), 201

    app.logger.warn(form.errors)
    return jsonify({"success": False, "errors": form.errors}), 400
