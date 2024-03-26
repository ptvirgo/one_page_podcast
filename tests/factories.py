# -*- coding: utf-8 -*-

import factory
import factory.fuzzy

from uuid import uuid4
from datetime import date

from opp.podcast import Channel, AudioFormat, Enclosure, Episode


class ChannelFactory(factory.Factory):
    class Meta:
        model = Channel
    
    title = factory.Faker("sentence", nb_words=3)
    link = factory.Faker("url")
    description = factory.Faker("sentence", nb_words=8)

    image = factory.Faker("file_name", extension="jpg")
    author = factory.Faker("name")
    email = factory.Faker("ascii_email")


class EpisodeFactory(factory.Factory):
    class Meta:
        model = Episode

    title = factory.Faker("sentence", nb_words=3)
    link = factory.Faker("url")
    description = factory.Faker("sentence", nb_words=8)
    guid = factory.LazyFunction(uuid4)
    duration = factory.Faker("random_int")
    enclosure = factory.SubFactory("tests.factories.EnclosureFactory")

    pubDate = factory.Faker("date_between")


class EnclosureFactory(factory.Factory):
    class Meta:
        model = Enclosure

    file_name = factory.Faker("file_name")
    audio_format = factory.fuzzy.FuzzyChoice(AudioFormat)
    length = factory.fuzzy.FuzzyInteger(1000, 10000)
