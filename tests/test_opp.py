#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import opp
from .factories import EpisodeFactory


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
