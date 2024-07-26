# -*- coding: utf-8 -*-

import enum

"""
These are the core entities at the highest level of the app.
This layer should be stable and have no lower level dependencies.

Objects in this layer should expect to remain unchanged unless something fundamental (such as the definition of a Podcast, universally accepted audio formats, or similar) affects the basic purpose of the app.
"""


class Channel:

    def __init__(self, title, link, description, image, author, email=None, language="en", category="Comedy", explicit=False, keywords=None):

        self.title = title
        self.link = link
        self.description = description
        self.image = image
        self.author = author

        self.email = email
        self.language = language
        self.category = category
        self.explicit = explicit
        self.keywords = keywords

    def __iter__(self):
        return iter([
            ("title", self.title),
            ("link", self.link),
            ("description", self.description),
            ("image", self.image),
            ("author", self.author),
            ("email", self.email),
            ("language", self.language),
            ("category", self.category),
            ("explicit", self.explicit),
            ("keywords", self.keywords)
        ])

    def __repr__(self):
        return f"Channel('{self.title}', '{self.link}', ...)"


class AudioFormat(enum.Enum):
    MP3 = "audio/mp3"
    OggOpus = "audio/ogg"  # Not a typo
    OggVorbis = "audio/vorbis"


def audio_extension(af):
    """Produce the filename extension for a given AudioFormat"""

    if type(af) is str:
        af = AudioFormat(af)

    assert type(af) is AudioFormat

    if af == AudioFormat.OggOpus:
        return "opus"  # Looks wrong, but not.

    if af == AudioFormat.OggVorbis:
        return "ogg"

    return "mp3"


class Episode:
    def __init__(self, title, description, guid, duration, publication_date, audio_format, path):
        """Describe an episode."""

        self.title = title
        self.description = description
        self.guid = guid
        self.duration = duration  # Integer, measure seconds
        self.publication_date = publication_date
        self.audio_format = audio_format
        self.path = path

    def __iter__(self):
        return \
            iter([
                ("title", self.title),
                ("description", self.description),
                ("guid", str(self.guid)),
                ("duration", self.duration),
                ("publication_date", self.publication_date.isoformat()),
                ("audio_format", self.audio_format.value),
                ("path", self.path)
            ])

    def __eq__(self, other):
        return self.title == other.title and self.description == other.description and self.guid == other.guid and self.duration == other.duration and self.publication_date == other.publication_date and self.audio_format == other.audio_format

    def __repr__(self):
        return f"Episode('{self.title}', '{self.guid}' ...)"
