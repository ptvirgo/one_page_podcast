# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
import mutagen
from uuid import uuid4

from .podcast import Channel, AudioFormat

"""
Administrator use case code & interface definition.

Changes to the operation of the application, that the owner, would be reflected here.  However, this layer should not affect the core entities nor should it be impacted by the UI or any databases, etc.
"""


class PodcastDatastore(ABC):

    """Provide a dependency inversion layer so that arbitrary data-storage backends can be made compatible with the administrator's use-cases."""

    @abstractmethod
    def initialize_channel(self, title, link, description, image, author, email, language, category, explicit, keywords):
        """Initialize a new channel."""
        pass

    @abstractmethod
    def get_channel(self):
        """Produce the podcast.Channel."""
        pass

    @abstractmethod
    def update_channel(self, title, link, description, image, author, email, language, category, explicit, keywords):
        """Update the externally stored podcast channel information."""
        pass

    @abstractmethod
    def create_episode(self, input_file_handle, title, description, guid, duration, publication_date, audio_format, length):
        """Save a new episode."""
        pass

    @abstractmethod
    def get_episodes(self):
        """Produce an iterable of podcast.Episodes."""
        pass

    @abstractmethod
    def update_episode(self, guid, title=None, description=None, duration=None, publication_date=None):
        """Update an existing episode."""
        pass

    @abstractmethod
    def delete_episode(self, guid):
        """Delete an episode.""show " = """
        pass


class AdminPodcast:

    """Provide the high level CRUD related use-case interface for the administrative user."""

    def __init__(self, datastore):
        self.datastore = datastore

    def initialize_channel(self, title, link, description, image, author, email, language, category, explicit, keywords):
        channel = Channel(title, link, description, image, author, email, language, category, explicit, keywords)
        self.datastore.initialize_channel(channel.title, channel.link, channel.description, channel.image, channel.author, channel.email, channel.language, channel.category, channel.explicit, channel.keywords)

    def get_channel(self):
        channel = self.datastore.get_channel()
        return dict(channel)

    def update_channel(self, title=None, link=None, description=None, image=None, author=None, email=None, language=None, category=None, explicit=None, keywords=None):

        previous = self.datastore.get_channel()

        if explicit is None:
            explicit = previous.explicit

        if keywords is None:
            keywords = previous.keywords

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

    def create_episode(self, input_file_handle, title, description, duration, publication_date, audio_format, length):
        """Save a new episode."""

        guid = uuid4()
        audio_format = AudioFormat(audio_format)  # minimal validation

        self.datastore.create_episode(input_file_handle, title, description, str(guid), duration, publication_date, audio_format.value, length)

        return str(guid)

    def get_episodes(self):
        """Produce an iterable of episode data in dicts."""
        return [dict(ep) for ep in self.datastore.get_episodes()]

    def update_episode(self, guid, title=None, description=None, duration=None, publication_date=None, audio_format=None):
        """Update an existing episode."""

        self.datastore.update_episode(guid, title=title, description=description, duration=duration, publication_date=publication_date)

    def delete_episode(self, guid):
        """Delete an episode."""
        self.datastore.delete_episode(guid)

    def extract_details(self, filehandle):
        """
        Attempt to extract the following from an audio file:
        - duration
        - audio format
        - description
        - length
        """

        audio_file = mutagen.File(filehandle)

        format_name = audio_file.mime[0]

        if format_name == "audio/vorbis":
            audio_format = AudioFormat.OggVorbis

        elif format_name == "audio/ogg":
            audio_format = AudioFormat.OggOpus

        else:
            audio_format = AudioFormat.MP3

        duration = round(audio_file.info.length)

        filehandle.seek(0, 2)
        length = filehandle.tell()
        filehandle.seek(0)

        if audio_format == AudioFormat.MP3:
            title = audio_file.tags.get("TIT2")
            description = audio_file.tags.get("TXXX:description")
        else:
            title = audio_file.tags.get("title")
            description = audio_file.tags.get("description")

        if type(title) is list:
            title = title[0]

        if type(description) is list:
            description = description[0]

        return {"audio_format": audio_format.value,
                "duration": duration,
                "title": str(title),
                "description": str(description),
                "length": length,
                }
