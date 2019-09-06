#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import io
import json
import os
import unittest

import opp

from .factories import EpisodeFactory

TEST_PATH = os.path.dirname(os.path.abspath(__file__))

if opp.db.engine.has_table("episode"):
    raise RuntimeError("Previous database exists.  If you're sure you're "
                       "using a test database, delete it.")
else:
    opp.app.testing = True
    opp.app.config["JWT_COOKIE_CSRF_PROTECT"] = False


class TestWithDatabase(unittest.TestCase):
    """
    Provide TestCase framework with a fresh opp database
    """
    @classmethod
    def setUp(self, *args, **kwargs):
        opp.db.create_all()

    @classmethod
    def tearDown(self, *args, **kwargs):
        opp.db.drop_all()


class TestHelpers(unittest.TestCase):
    """
    Test helpers
    """
    def test_audio_file_name(self):
        published = datetime(2019, 9, 2, 22, 50, 15)
        title = "It could / couldn't be the title, etc."
        af_format = opp.AudioFormat.MP3

        self.assertEqual(opp.audio_file_name(published, title, af_format),
                         "2019-09-02-it_could_couldnt_be_the_title_etc.mp3")


class TestFormatters(unittest.TestCase):
    """
    Validate the output formatters
    """
    def test_format_duration(self):
        """
        Make duration is formatted correctly
        """
        self.assertEqual(opp.format_duration(3), "03")
        self.assertEqual(opp.format_duration(59), "59")
        self.assertEqual(opp.format_duration(90), "01:30")
        self.assertEqual(opp.format_duration(3750), "01:02:30")


class TestLogin(TestWithDatabase):
    """
    Validate routes
    """
    def test_login_produces_jwt(self):
        """
        Make sure a correct login will work.
        """
        login = json.dumps(dict(
            username=opp.SETTINGS["configuration"]["admin"]["username"],
            password=opp.SETTINGS["configuration"]["admin"]["password"]))

        with opp.app.test_client() as client:
            res = client.post(
                "/admin/login", data=login, content_type="application/json")

        self.assertEqual(res.status, "200 OK")
        self.assertTrue(res.is_json)

        self.assertIsNot(res.json.get("jwt"), None)
        self.assertIs(res.json.get("msg"), None)

    def test_invalid_login_produces_401(self):
        """
        Make sure an invalid login will get a 401 response
        """
        login = json.dumps(dict(
            username=opp.random_text(8),
            password=opp.random_text(8)))

        with opp.app.test_client() as client:
            res = client.post(
                "/admin/login", data=login, content_type="application/json")

        self.assertEqual(res.status, "401 UNAUTHORIZED")
        self.assertTrue(res.is_json)

        self.assertIs(res.json.get("jwt"), None)
        self.assertEqual(res.json.get("msg"), "Invalid credentials")

    def test_login_without_credentials_produces_400(self):
        """
        Make sure a login without credentials will get a 400 response
        """
        def validate_result(login):
            with opp.app.test_client() as client:
                res = client.post("/admin/login", data=json.dumps(login),
                                  content_type="application/json")

            self.assertEqual(res.status, "400 BAD REQUEST")
            self.assertTrue(res.is_json)

            self.assertIs(res.json.get("jwt"), None)
            self.assertEqual(res.json.get("msg"), "Missing credentials")

        validate_result({})
        validate_result({"username": opp.random_text(8)})
        validate_result({"password": opp.random_text(8)})


class TestApi(TestWithDatabase):
    """
    Validate CRUD operations for the administrator's API
    """
    def logged_in_client(self):
        """
        Return a logged in client
        """
        username = opp.SETTINGS["configuration"]["admin"]["username"]
        password = opp.SETTINGS["configuration"]["admin"]["password"]
        data = {"username": username, "password": password}

        client = opp.app.test_client()
        response = client.post(
            "/admin/login", mimetype="application/json",
            data=json.dumps(data))

        return client

    def new_episode_post_data(self, episode, audio_file):
        """
        Produce the expected post data for a given episode & audio file
        """
        data = {
            "title": episode.title,
            "published": datetime.fromtimestamp(episode.published.timestamp()),
            "description": episode.description,
            "keywords": opp.format_episode_keywords(episode.keywords),
            "audio_file": audio_file
        }

        if episode.explicit:
            data["explicit"] = True

        return data

    def test_validate_audio_file(self):
        """
        Ensure invalid audio files are rejected
        """
        episode = EpisodeFactory()
        bad_data = io.BytesIO(b"this better not work")
        data = self.new_episode_post_data(episode, bad_data)

        with self.logged_in_client() as client:
            response = client.post("/admin/episode/new", buffered=True, data=data,
                                   content_type="multipart/form-data")

        self.assertEqual(response.status, "400 BAD REQUEST")
        file_path = os.path.join(
            opp.SETTINGS["configuration"]["directories"]["media"],
            opp.audio_file_name(data["published"], data["title"],
                                opp.AudioFormat.MP3))
        self.assertFalse(os.path.exists(file_path))
        self.assertIs(opp.Episode.query.filter_by(
            title=data["title"]).first(), None)

    def test_create_episode(self):
        """
        Verify administrator can create a new episode
        """
        episode = EpisodeFactory()
        stored = opp.Episode.query.filter_by(title=episode.title).first()
        self.assertIs(stored, None,
                      msg="Factory should not have created database entry")

        fn = os.path.join(TEST_PATH, "data", "episode_01.opus")

        with open(fn, "rb") as audio_file:
            data = self.new_episode_post_data(episode, audio_file)

            with self.logged_in_client() as client:
                response = client.post(
                    "/admin/episode/new", buffered=True, data=data,
                    content_type="multipart/form-data")

        # Good response?
        self.assertEqual(response.status, "201 CREATED")

        # Data stored correctly?
        stored = opp.Episode.query.filter_by(title=episode.title).first()
        self.assertEqual(stored.title, data["title"])
        self.assertEqual(stored.published, data["published"])
        self.assertEqual(stored.description, data["description"])
        self.assertEqual(stored.explicit, episode.explicit)

        # File created?
        fn = opp.audio_file_name(data["published"], data["title"],
                                 opp.AudioFormat.OggOpus)
        file_path = os.path.join(
            opp.SETTINGS["configuration"]["directories"]["media"], fn)
        self.assertTrue(os.path.exists(file_path))
        os.remove(file_path)

    def test_create_requires_login(self):
        """
        Ensure that only a logged in admin can create episodes
        """
        # Getting the episode creation page without authentication is blocked
        with opp.app.test_client() as client:
            response = client.get("/admin/episode/new")
        self.assertEqual(response.status, "401 UNAUTHORIZED")

        # Posting to the create api wouthout authentication is blocked
        episode = EpisodeFactory()
        fn = os.path.join(TEST_PATH, "data", "episode_01.opus")

        with open(fn, "rb") as audio_file:
            data = self.new_episode_post_data(episode, audio_file)

            with opp.app.test_client() as client:
                response = client.post(
                    "/admin/episode/new", buffered=True, data=data,
                    content_type="multipart/form-data")

        self.assertEqual(response.status, "401 UNAUTHORIZED")
        self.assertIs(
            opp.Episode.query.filter_by(title=episode.title).first(), None)

        fn = opp.audio_file_name(data["published"], data["title"],
                                 opp.AudioFormat.OggOpus)
        file_path = os.path.join(
            opp.SETTINGS["configuration"]["directories"]["media"], fn)
        self.assertFalse(os.path.exists(file_path))
