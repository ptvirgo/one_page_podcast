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
    def update_channel(self, title, link, description, image, author, email, language, category, explicit, keywords):
        """Update the externally stored podcast channel information."""
        pass


    @abstractmethod
    def create_episode(self, title, link, description, guid, duration, pubDate, file_name, audio_format, length, image=None):
        """Save a new episode."""
        pass

    @abstractmethod
    def get_episodes(self):
        """Produce an iterable of podcast.Episodes."""
        pass

    @abstractmethod
    def update_episode(self, guid, title=None, link=None, description=None, duration=None, pubDate=None, file_name=None, audio_format=None, length=None, image=None):
        """Update an existing episode."""
        pass

    @abstractmethod
    def delete_episode(self, guid):
        """Delete an episode.""show " = """
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

        previous = as_channel(self.datastore.get_channel())

        if explicit is None:
            explicit = previous.explicit

        if keywords is None:
            kepwords = previous.keywords

        new = Channel(
            title or previous.title,
            link or previous.link,
            description or previous.description,
            image or previous.image,
            author or previous.author,
            email or previous.email,
            language or previous.language,
            category or previous.category,
            explicit,
            keywords
        )

        self.datastore.update_channel(title=new.title, link=new.link, description=new.description, image=new.image, author=new.author, email=new.email, language=new.language, category=new.category, explicit=new.explicit, keywords=new.keywords)

    def create_episode(self, title, link, description, guid, duration, pubDate, file_name, audio_format, length, image=None):
        """Save a new episode."""

        enclosure = Enclosure(file_name, AudioFormat(audio_format), length)
        new = Episode(title, link, description, guid, duration, enclosure, pubDate, image=image)

        self.datastore.create_episode(new.title, new.link, new.description, new.guid, new.duration, new.pubDate, new.enclosure.file_name, new.enclosure.audio_format.value, new.enclosure.length, image=new.image)

    def get_episodes(self):
        """Produce an iterable of podcast.Episodes."""
        episodes = [ as_episode(ep) for ep in self.datastore.get_episodes() ]
        return [ ep.as_dict() for ep in episodes ]

    def update_episode(self, guid, title=None, link=None, description=None, duration=None, pubDate=None, file_name=None, audio_format=None, length=None, image=None):
        """Update an existing episode."""

        if pubDate is not None:
            pubDate = date.fromisoformat(pubDate)

        self.datastore.update_episode(guid, title=title, link=link, description=description, duration=duration, pubDate=pubDate, file_name=file_name, audio_format=audio_format, length=length, image=image)

    def delete_episode(self, guid):
        """Delete an episode."""
        self.datastore.delete_episode(guid)
