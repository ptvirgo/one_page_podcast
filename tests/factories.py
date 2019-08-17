# -*- coding: utf-8 -*-

import factory
import factory.fuzzy
import random

from opp import Episode, Keyword

class EpisodeFactory(factory.Factory):
    class Meta:
        model = Episode

    title = factory.Faker("sentence", nb_words=3)
    published = factory.Faker("date_time")
    description = factory.Faker("sentence", nb_words=8)
    image = factory.Faker("file_name", extension="jpg")
    explicit = factory.fuzzy.FuzzyChoice([True, False])

    @factory.lazy_attribute
    def keywords(self):
        return [KeywordFactory(), KeywordFactory(), KeywordFactory()]

class KeywordFactory(factory.Factory):
    class Meta:
        model = Keyword
    word = factory.Faker("color_name")
