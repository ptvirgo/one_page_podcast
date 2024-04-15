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
        """
        Produce a dict describing the podcast channel, as follows:

            {
                title: str
                link: str, url
                description: str
                image: image url
                author: str
                email: str, email address
                language: "en" or similar language code
                category: str - Apple podcast defines a limited set
                explicit: boolean
                keywords: list of strings
            }

        """
        pass


    @abstractmethod
    def get_episodes(self):
        """
        Produce an iterable of podcast episode descriptors, as follows:

            [
                {
                    title: str
                    link: str, url
                    description: str
                    guid: str, globally unique identifier
                    duration: int, seconds

                    pubDate: iso formatted date string
                    image: str, url
               
                    file_name: str url
                    audio_format: str, "mp3", "ogg", "opus"
                    length: int, bytes
                }
            ]

        """
        pass


class VisitPodcast:

    def __init__(self, loader):
        self.loader = loader
        self.channel = self.loader.get_channel()
        self.episodes = self.loader.get_episodes()

    def podcast_data(self):
        """Produce a dict of all fields needed to follow the podcast."""

        return \
            { "channel":
                {
                    "title": self.channel.title,
                    "link": self.channel.link,
                    "description": self.channel.description,
                    "image": self.channel.image,
                    "author": self.channel.author,
                    "email": self.channel.email,
                    "language": self.channel.language,
                    "category": self.channel.category,
                    "explicit": self.channel.explicit,
                    "keywords": self.channel.keywords
                },
                "episodes": [ dict(ep) for ep in self.episodes ]
            }
