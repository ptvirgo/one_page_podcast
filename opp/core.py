# -*- coding: utf-8 -*-

from copy import deepcopy
from datetime import datetime
import markdown
import os
import pytz
import yaml

from flask import Flask, Response, jsonify, make_response, redirect, \
    render_template, request, send_from_directory, url_for
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, \
     get_jwt_identity, set_access_cookies, unset_jwt_cookies, config

from .helpers import random_text
from .models import db, Episode, AudioFile, AudioFormat, Keyword
from .forms import LoginForm, CreateEpisodeForm, DeleteEpisodeForm, UpdateEpisodeForm

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
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.config["JWT_ACCESS_COOKIE_PATH"] = "/admin"

app.config["WTF_CSRF_ENABLED"] = False

JWT = JWTManager(app)

db.init_app(app)

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


# - Administrative API

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    """
    Allow site administrator to log in
    """
    def login_page(form, error=None):
        if error is None:
            status = 200
        else:
            status = 401

        podcast = deepcopy(SETTINGS["podcast"])
        resp = make_response(render_template(
            "admin/login.html", form=form, podcast=podcast, error=error))
        unset_jwt_cookies(resp)
        return resp, status

    username = SETTINGS["configuration"]["admin"]["username"]
    password = SETTINGS["configuration"]["admin"]["password"]
    form = LoginForm(username, password)

    if request.method == "GET":
        return login_page(form)

    if form.validate_on_submit():
        resp = redirect(url_for("episode_list"))
        token = create_access_token(identity=form.username)
        set_access_cookies(resp, token)
        return resp, 303

    return login_page(form, error="Invalid credentials")


@app.route("/admin/episode/new", methods=["GET", "POST"])
@jwt_required
def episode_create():
    """
    Allow administrator to create new episodes
    """
    def page(form, error=None):
        podcast = deepcopy(SETTINGS["podcast"])
        return render_template(
            "admin/create.html", form=form, podcast=podcast, error=error)
        
    form = CreateEpisodeForm(SETTINGS["configuration"]["directories"]["media"])

    if request.method == "GET":
        return page(form), 200

    if form.validate_on_submit():
        episode = form.create_episode()

        try:
            db.session.add(episode)
            db.session.commit()
        except Exception as error:
            app.logger.error("Failed to save episode: %s" % str(error))
            file_path = os.path.join(form.media_dir,
                                     episode.audio_file.file_name)
            os.remove(file_path)
            return page(form, error="Failed to save episode, see log"), 500

        return redirect(url_for("episode_list")), 303

    return page(form), 400


@app.route("/admin/episodes", methods=["GET"])
@jwt_required
def episode_list():
    """
    List available episodes for the admin
    """
    podcast = deepcopy(SETTINGS["podcast"])
    episodes = Episode.query.order_by(Episode.published.desc()).all()

    return render_template(
        "admin/episodes.html", podcast=podcast, episodes=episodes), 200


@app.route("/admin/episode/<int:episode_id>", methods=["GET", "POST"])
@jwt_required
def episode_admin(episode_id):
    """
    Allow admin to update episodes
    """
    def page(episode, form):
        podcast = deepcopy(SETTINGS["podcast"])
        return render_template(
            "admin/episode.html", episode=episode, form=form, podcast=podcast)

    time_zone = pytz.timezone(SETTINGS["configuration"]["timezone"])
    form = UpdateEpisodeForm(time_zone)
    episode = Episode.query.filter_by(item_id=episode_id).first()

    if episode is None:
        return "Not found", 404

    if request.method == "GET":
        return page(episode, form), 200

    if form.validate_on_submit():
        episode = form.update_episode(episode)
        db.session.commit()

        return page(episode, form), 200

    return page(episode, form), 400


@app.route("/admin/episode/<int:episode_id>/delete", methods=["POST"])
@jwt_required
def episode_delete(episode_id):
    """
    Allow admin to delete episodes
    """
    form = DeleteEpisodeForm()

    episode = Episode.query.filter_by(item_id=episode_id).first()

    if episode is None:
        return "Not found", 404

    if form.validate_on_submit():
        file_path = os.path.join(
            SETTINGS["configuration"]["directories"]["media"],
            episode.audio_file.file_name)

        db.session.delete(episode)
        db.session.commit()
        os.remove(file_path)

        return redirect(url_for("episode_list")), 303

    return "Confirmation required", 400
