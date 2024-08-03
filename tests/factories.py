# -*- coding: utf-8 -*-

import factory
import factory.fuzzy

from uuid import uuid4
from pathlib import Path
from opp.podcast import Channel, AudioFormat, Episode


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
    description = factory.Faker("sentence", nb_words=8)
    guid = factory.LazyFunction(uuid4)
    duration = factory.Faker("random_int")
    publication_date = factory.Faker("date_between")
    audio_format = factory.fuzzy.FuzzyChoice(AudioFormat)
    path = factory.LazyAttribute(lambda ep: Path(str(ep.guid)))
    length = factory.fuzzy.FuzzyInteger(5000, 25000)
