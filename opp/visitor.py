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

def as_channel(channel_input):
    return Channel(
            channel_input["title"],
            channel_input["link"],
            channel_input["description"],
            channel_input["image"],
            channel_input["author"],
            email=channel_input["email"],
            language=channel_input["language"],
            category=channel_input["category"],
            explicit=channel_input["explicit"],
            keywords=channel_input["keywords"]
        )


def as_episode(ep):
    enclosure = Enclosure(
            ep["file_name"],
            AudioFormat(ep["audio_format"]),
            ep["length"]
        )

    episode = Episode(
            ep["title"],
            ep["link"],
            ep["description"],
            ep["guid"],
            ep["duration"],
            enclosure,
            date.fromisoformat(ep["pubDate"]),
            image=ep["image"]
        )

    return episode


class VisitPodcast:

    def __init__(self, loader):
        self.loader = loader
        self.channel = as_channel(self.loader.get_channel())
        self.episodes = [ as_episode(x) for x in self.loader.get_episodes() ]

    # You probably think the conversion to a dict is not very DRY. However, the purpose of this layer is to create a dependency inversion and establish a boundary between the (tiny) core application and the I/O layers. Clean Architecture, pp 189.

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
                "episodes": [ e.as_dict() for e in self.episodes ]
            }
