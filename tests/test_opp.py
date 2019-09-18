#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import io
import json
import os
import unittest
import random

import opp

from .factories import EpisodeFactory

TEST_PATH = os.path.dirname(os.path.abspath(__file__))

if opp.db.engine.has_table("episode"):
    raise RuntimeError("Previous database exists.  If you're sure you're "
                       "using a test database, delete it.")
else:
    opp.app.testing = True
    opp.app.config["JWT_COOKIE_CSRF_PROTECT"] = False


class WithDatabase:
    """
    Provide a TestCase with a prepared database
    """
    @classmethod
    def setUp(self, *args, **kwargs):
        opp.db.create_all()

    @classmethod
    def tearDown(self, *args, **kwargs):
        opp.db.drop_all()


class WithLoggedInClient:
    """
    Provide a TestCase with an authenticated client
    """
    def logged_in_client(self):
        """
        Return a logged in client
        """
        username = opp.SETTINGS["configuration"]["admin"]["username"]
        password = opp.SETTINGS["configuration"]["admin"]["password"]
        data = {"username": username, "password": password}

        client = opp.app.test_client()
        client.post("/admin/login", mimetype="application/json",
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


class TestLogin(WithDatabase, WithLoggedInClient, unittest.TestCase):
    """
    Validate routes
    """
    def test_login_produces_jwt(self):
        """
        Make sure a correct login will work.
        """
        login = {
            "username": opp.SETTINGS["configuration"]["admin"]["username"],
            "password": opp.SETTINGS["configuration"]["admin"]["password"]
        }

        with opp.app.test_client() as client:
            res = client.post("/admin/login", data=login)

        self.assertEqual(res.status, "200 OK")
        self.assertTrue(res.is_json)

        self.assertIsNot(res.json.get("jwt"), None)
        self.assertIs(res.json.get("msg"), None)

    def prove_login_is_invalid(self, login):
        """
        Verify that given login credintials produce a 401 response
        """
        with opp.app.test_client() as client:
            res = client.post("/admin/login", data=login)

        self.assertEqual(res.status, "401 UNAUTHORIZED")
        self.assertTrue(res.is_json)

        self.assertIs(res.json.get("jwt"), None)
        self.assertEqual(res.json.get("msg"), "Invalid credentials")

    def test_invalid_login_produces_401(self):
        """
        Make sure an invalid login will get a 401 response
        """
        login = {
            "username": opp.random_text(8),
            "password": opp.random_text(8)
        }
        self.prove_login_is_invalid(login)

    def test_login_without_credentials_produces_400(self):
        """
        Make sure a login without credentials will get a 400 response
        """
        self.prove_login_is_invalid({"username": opp.random_text(8)})
        self.prove_login_is_invalid({"password": opp.random_text(8)})


class TestApiCreate(WithDatabase, WithLoggedInClient, unittest.TestCase):
    """
    Validate CRUD operations for the administrator's API
    """
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


class TestApiRead(WithDatabase, WithLoggedInClient, unittest.TestCase):
    def test_list_episodes(self):
        """
        API can list multiple episodes as JSON
        """
        episodes = []
        now = datetime.now()

        for i in range(5):
            days = timedelta(days=i)
            ep = EpisodeFactory(published=now - days)
            opp.db.session.add(ep)
            opp.db.session.commit()
            episodes.append(dict(ep))

        with self.logged_in_client() as client:
            res = client.get("/admin/episodes")

        self.assertTrue(res.is_json)

        jsr = res.json
        for i in range(5):
            returned = jsr[i]
            returned.pop("url")
            returned["audio_file"].pop("url")

            self.assertEqual(returned, episodes[i])

    def test_read_episode(self):
        """
        API delivers single episode as JSON
        """
        episode = EpisodeFactory()
        opp.db.session.add(episode)
        opp.db.session.commit()
        data = dict(episode)

        with self.logged_in_client() as client:
            res = client.get("/admin/episode/%d" % episode.item_id)

        self.assertTrue(res.is_json)

        jsr = res.json
        jsr.pop("url")
        jsr["audio_file"].pop("url")

        self.assertEqual(jsr, data)

    def test_not_found(self):
        """
        API produces JSON 404 when called with incorrect item_id, for all call
        types
        """
        def is_404(res):
            self.assertTrue(res.is_json)
            self.assertEqual(res.status, "404 NOT FOUND")
            self.assertEqual(res.json["msg"], "episode not found")

        with self.logged_in_client() as client:
            url = "/admin/episode/%d" % random.randint(1, 10)
            is_404(client.get(url))
            is_404(client.put(url, data={}))
            is_404(client.delete(url))


class TestApiUpdate(WithDatabase, WithLoggedInClient, unittest.TestCase):
    """
    Ensure updating works
    """
    def test_update_episode(self):
        """
        API allows detail updates.
        """
        def make_update(item_id, attr, value):
            url = "/admin/episode/%d" % item_id
            data = {attr: value}

            with self.logged_in_client() as client:
                client.put(url, data=data)

        def test_update(item_id, attr, value):
            make_update(item_id, attr, value)
            res = opp.Episode.query.filter_by(item_id=item_id).first()

            msg = "attribute %s failed to update" % attr
            self.assertEqual(getattr(res, attr), value, msg=msg)

            return res

        ep = EpisodeFactory()
        opp.db.session.add(ep)
        opp.db.session.commit()
        ep = opp.Episode.query.filter_by(title=ep.title).first()
        item_id = ep.item_id

        after = EpisodeFactory(explicit=not ep.explicit)

        for attr in ["title", "description", "explicit"]:
            test_update(item_id, attr, getattr(after, attr))

        make_update(item_id, "published", after.published.isoformat())
        res = opp.Episode.query.filter_by(item_id=item_id).first()
        self.assertEqual(res.published.timestamp(), after.published.timestamp())

        kws = opp.format_episode_keywords(after.keywords)
        make_update(item_id, "keywords", kws)
        res = opp.Episode.query.filter_by(item_id=item_id).first()
        self.assertEqual(opp.format_episode_keywords(res.keywords), kws)

        raise NotImplementedError("Test that updates ONLY change requested fields")


class TestApiDelete(WithDatabase, WithLoggedInClient, unittest.TestCase):
    """
    I can haz delete
    """
    def test_delete_episode(self):
        episode = EpisodeFactory()
        fn = os.path.join(TEST_PATH, "data", "episode_01.opus")

        with open(fn, "rb") as audio_file:
            data = self.new_episode_post_data(episode, audio_file)
            data = self.new_episode_post_data(episode, audio_file)

            with self.logged_in_client() as client:
                client.post(
                    "/admin/episode/new", buffered=True, data=data,
                    content_type="multipart/form-data")

        res = opp.Episode.query.filter_by(title=episode.title).first()
        item_id = res.item_id
        path = res.audio_file.abs_path

        self.assertIsNot(item_id, None)
        self.assertTrue(os.path.exists(path))

        with self.logged_in_client() as client:
            client.delete("/admin/episode/%d" % item_id)

        res = opp.Episode.query.filter_by(item_id=item_id).first()
        self.assertEqual(res, None)
        self.assertFalse(os.path.exists(path))
