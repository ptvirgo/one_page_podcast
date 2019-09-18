# -*- coding: utf-8 -*-

from copy import deepcopy
from datetime import datetime
import enum
import markdown
import mutagen
import os
import io
import pytz
import yaml

from flask import Flask, Response, jsonify, render_template, request, \
     send_from_directory, url_for
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, \
     get_jwt_identity, set_access_cookies, unset_jwt_cookies, config
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
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = True
app.config["JWT_COOKIE_CSRF_PROTECT"] = True
app.config['JWT_ACCESS_COOKIE_PATH'] = "/admin"

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
    return ",".join(sorted([kw.word for kw in kws]))


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

    def set_keywords(self, words):
        """Replace self.keywords with newly provided words"""
        for kw in self.keywords:
            self.keywords.remove(kw)

        for word in words:
            kw = Keyword.query.filter_by(word=word).first()

            if kw is None:
                kw = Keyword(word=word)

            self.keywords.append(kw)

    def __repr__(self):
        return "<Episode %s, %s>" % (self.published.isoformat(), self.title)

    def __iter__(self):
        """Produce iterable of attributes"""
        return iter([
            ("item_id", self.item_id),
            ("title", self.title),
            ("published", self.published.isoformat()),
            ("description", self.description),
            ("image", getattr(self, "image", None)),
            ("explicit", self.explicit),
            ("audio_file", dict(self.audio_file)),
            ("keywords", [kw.word for kw in self.keywords])])


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

    @staticmethod
    def path_for(file_name):
        return os.path.join(
            SETTINGS["configuration"]["directories"]["media"], file_name)

    @property
    def abs_path(self):
        return self.path_for(self.file_name)

    def __repr__(self):
        return "<AudioFile %s>" % self.file_name

    def __iter__(self):
        """Produce iterable of attributes"""
        return iter([
            ("item_id", self.item_id),
            ("file_name", self.file_name),
            ("audio_format", self.audio_format.value),
            ("length", self.length),
            ("duration", self.duration)])


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
        AudioFile.path_for(filename), as_attachment=False)


# - Administrative API

class LoginForm(FlaskForm):
    """
    Provide a log in form
    """
    username = form.StringField(
        label="Username", validators=[validator.DataRequired()])
    password = form.PasswordField(
        label="Password", validators=[validator.DataRequired()])


@app.route("/admin/login", methods=["POST"])
def login():
    """
    Allow site administrator to log in
    """
    def valid_login(username, password):
        return username == SETTINGS["configuration"]["admin"]["username"] and \
               password == SETTINGS["configuration"]["admin"]["password"]

    form = LoginForm()

    if form.validate_on_submit() and valid_login(
            form.username.data, form.password.data):

        token = create_access_token(identity=form.username)
        resp = jsonify({"jwt": token, "success": True})
        set_access_cookies(resp, token)
        return resp, 200

    return jsonify({"success": False, "msg": "Invalid credentials"}), 401


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
    explicit = form.BooleanField(
        label="Explicit", false_values=("false", "False", ""))
    keywords = form.StringField(
        label="Keywords", validators=[validator.Optional()])
    audio_file = FileField(
        label="Audio file", validators=[FileRequired()])


@app.route("/admin/episode/new", methods=["GET", "POST"])
@jwt_required
def episode_create():
    """
    Allow administrator to create new episodes
    """
    if request.method == "GET":
        return render_template("admin/create.html")

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

        af_path = AudioFile.path_for(af_name)

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
            words = form.keywords.data.split(",")
            episode.set_keywords(words)

        db.session.add(episode)
        db.session.commit()

        return jsonify({"success": True}), 201

    app.logger.warning(form.errors)
    return jsonify({"success": False, "msg": form.errors}), 400


def episode_json(episode):
    """
    Produce the JSON representation of an episode
    """
    entry = dict(episode)
    entry["url"] = url_for("episode_admin", episode_id=episode.item_id)
    entry["audio_file"]["url"] = url_for(
        "media", filename=episode.audio_file.file_name, _external=True)
    return entry


@app.route("/admin/episodes", methods=["GET"])
@jwt_required
def episode_list():
    """
    Produce the episode data in json format
    """
    episodes = Episode.query.order_by(Episode.published.desc()).all()
    data = [episode_json(ep) for ep in episodes]
    return jsonify(data), 200


class UpdateEpisodeForm(FlaskForm):
    """
    Provide a form for updating episodes
    """
    title = form.StringField(
        label="Title", validators=[validator.Optional()])
    published = DateTimeField(
        label="Publication date & time", validators=[validator.Optional()])
    description = form.StringField(
        label="Description", validators=[validator.Optional()])
    explicit = form.BooleanField(
        label="Explicit", false_values=("false", "False", ""))
    keywords = form.StringField(
        label="Keywords", validators=[validator.Optional()])


@app.route("/admin/episode/<int:episode_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required
def episode_admin(episode_id):
    """
    Allow read, update, and delete operations on a single episode
    """
    episode = Episode.query.filter_by(item_id=episode_id).first()

    if episode is None:
        return jsonify({"success": False, "msg": "episode not found"}), 404

    if request.method == "GET":
        return episode_json(episode), 200

    if request.method == "PUT":
        form = UpdateEpisodeForm()

        if form.validate_on_submit():
            for attr in ["title", "description", "explicit"]:
                field = getattr(form, attr)

                if field.data is not None and field.data != "":
                    setattr(episode, attr, field.data)

            if form.published.data is not None:
                episode.published = datetime.fromtimestamp(
                    form.published.data.timestamp())

            if form.keywords.data is not None:
                words = form.keywords.data.split(",")
                episode.set_keywords(words)

            db.session.commit()
            return episode_json(episode), 200

    if request.method == "DELETE":
        os.remove(episode.audio_file.abs_path)
        db.session.delete(episode)
        db.session.commit()
        return jsonify({"success": True}), 200
