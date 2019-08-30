#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import json
import opp
from opp.helpers import random_text


if opp.db.engine.has_table("episode"):
    raise RuntimeError("Previous database exists.  If you're sure you're "
                       "using a test database, delete it.")
else:
    opp.app.testing = True


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


class TestRoutes(unittest.TestCase):
    """
    Validate routes
    """
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.client = opp.app.test_client()
        opp.db.create_all()

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        super().tearDownClass(*args, **kwargs)
        opp.db.drop_all()

    def test_login_produces_jwt(self):
        """
        Make sure a correct login will work.
        """
        login = json.dumps(dict(
            username=opp.SETTINGS["configuration"]["admin"]["username"],
            password=opp.SETTINGS["configuration"]["admin"]["password"]))

        res = self.client.post(
            "/login", data=login, content_type="application/json")

        self.assertEqual(res.status, "200 OK")
        self.assertTrue(res.is_json)

        self.assertIsNot(res.json.get("jwt"), None)
        self.assertIs(res.json.get("msg"), None)

    def test_invalid_login_produces_401(self):
        """
        Make sure an invalid login will get a 401 response
        """
        login = json.dumps(dict(
            username=random_text(8),
            password=random_text(8)))

        res = self.client.post(
            "/login", data=login, content_type="application/json")

        self.assertEqual(res.status, "401 UNAUTHORIZED")
        self.assertTrue(res.is_json)

        self.assertIs(res.json.get("jwt"), None)
        self.assertEqual(res.json.get("msg"), "Invalid credentials")

    def test_login_without_credentials_produces_400(self):
        """
        Make sure a login without credentials will get a 400 response
        """
        def validate_result(login):
            res = self.client.post("/login", data=json.dumps(login),
                                   content_type="application/json")

            self.assertEqual(res.status, "400 BAD REQUEST")
            self.assertTrue(res.is_json)

            self.assertIs(res.json.get("jwt"), None)
            self.assertEqual(res.json.get("msg"), "Missing credentials")

        validate_result({})
        validate_result({"username": random_text(8)})
        validate_result({"password": random_text(8)})
