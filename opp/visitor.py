# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from datetime import date

from .podcast import *

"""
Visitor use case code & interface definition.

Changes to the operation of the application, that affect non-administrative visitors, would be reflected here.  However, this layer should not affect the core entities nor should it be impacted by the UI or any databases, etc.
"""

class PodcastDatastore(ABC):

    @abstractmethod
    def get_channel(self):
        """Produce the podcast channel."""
        pass


    @abstractmethod
    def get_episodes(self):
        """Produce an iterable of podcast episodes."""
        pass


class VisitPodcast:

    def __init__(self, loader):
        self.loader = loader

    def podcast_data(self):
        """Produce a dict of all fields needed to follow the podcast."""

        channel = self.loader.get_channel()
        episodes = self.loader.get_episodes()

        return \
            { "channel":
                {
                    "title": channel.title,
                    "link": channel.link,
                    "description": channel.description,
                    "image": channel.image,
                    "author": channel.author,
                    "email": channel.email,
                    "language": channel.language,
                    "category": channel.category,
                    "explicit": channel.explicit,
                    "keywords": channel.keywords
                },
                "episodes": [ dict(ep) for ep in episodes ]
            }
