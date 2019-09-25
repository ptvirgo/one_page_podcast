# -*- coding: utf-8 -*-

import factory
import factory.fuzzy

from opp.models import Episode, Keyword, AudioFormat, AudioFile
import pytz


class EpisodeFactory(factory.Factory):
    class Meta:
        model = Episode

    title = factory.Faker("sentence", nb_words=3)
    published = factory.Faker("date_time", tzinfo=pytz.utc)
    description = factory.Faker("sentence", nb_words=8)
    image = factory.Faker("file_name", extension="jpg")
    explicit = factory.fuzzy.FuzzyChoice([True, False])
    audio_file = factory.SubFactory("tests.factories.AudioFileFactory")

    @factory.lazy_attribute
    def keywords(self):
        return [KeywordFactory(), KeywordFactory(), KeywordFactory()]


class AudioFileFactory(factory.Factory):
    class Meta:
        model = AudioFile

    audio_format = factory.fuzzy.FuzzyChoice(AudioFormat)
    length = factory.fuzzy.FuzzyInteger(1000, 10000)
    duration = factory.fuzzy.FuzzyInteger(30, 900)

    @factory.lazy_attribute
    def file_name(self):
        return factory.Faker("file_name",
                             extension=self.audio_format.name).generate()


class KeywordFactory(factory.Factory):
    class Meta:
        model = Keyword
    word = factory.Faker("color_name")
