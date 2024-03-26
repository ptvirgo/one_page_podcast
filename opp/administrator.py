# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from datetime import date

from .podcast import *

"""
Administrator use case code & interface definition.

Changes to the operation of the application, that the owner, would be reflected here.  However, this layer should not affect the core entities nor should it be impacted by the UI or any databases, etc.
"""

class PodcastDatastore(ABC):

    """Provide a dependency inversion layer so that arbitrary data-storage backends can be made compatible with the administrator's use-cases."""

    @abstractmethod
    def get_channel(self):
        """Produce the podcast.Channel."""
        pass

    @abstractmethod
    def update_channel(self, title=None, link=None, description=None, image=None, author=None, email=None, language=None, category=None, explicit=None, keywords=None):
        """Update the externally stored podcast channel information."""
        pass


    @abstractmethod
    def create_episode(self, title, link, description, guid, duration, enclosure, pubDate, image=None):
        """Save a new episode."""
        pass

    @abstractmethod
    def get_episodes(self):
        """Produce an iterable of podcast.Episodes."""
        pass

    @abstractmethod
    def update_episode(self, guid, title=None, link=None, description=None, duration=None, enclosure=None, pubDate=None, image=None):
        """Update an existing episode."""
        pass

    @abstractmethod
    def delete_episode(self, guid):
        """Delete an episode."""
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


class AdminPodcast:

    """Provide the high level CRUD related use-case interface for the administrative user."""

    def __init__(self, datastore):
        self.datastore = datastore

    def get_channel(self):
        channel = as_channel(self.datastore.get_channel())
        return channel.as_dict()

    def update_channel(self, title=None, link=None, description=None, image=None, author=None, email=None, language=None, category=None, explicit=None, keywords=None):
        pass

    def create_episode(self, title, link, description, guid, duration, enclosure, pubDate, image=None):
        """Save a new episode."""
        pass

    def get_episodes(self):
        """Produce an iterable of podcast.Episodes."""
        episodes = [ as_episode(ep) for ep in self.datastore.get_episodes() ]
        return [ ep.as_dict() for ep in episodes ]

    def update_episode(self, guid, title=None, link=None, description=None, duration=None, enclosure=None, pubDate=None, image=None):
        """Update an existing episode."""
        pass

    def delete_episode(self, guid):
        """Delete an episode."""
        pass
