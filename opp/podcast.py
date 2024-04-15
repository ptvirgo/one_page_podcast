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
    MP3 = "mp3"
    OggOpus = "opus"
    OggVorbis = "ogg"

    @property
    def mimetype(self):
        """Produce the mime-type for this audio format"""
        kvp = {
            AudioFormat.MP3: "audio/mpeg",
            AudioFormat.OggOpus: "audio/ogg",  # not a typo
            AudioFormat.OggVorbis: "audio/ogg"}

        return kvp[self]


class Enclosure:
    def __init__(self, file_name, audio_format, length):
    
        self.file_name = file_name
        self.audio_format = audio_format
        self.length = length # Integer, size in bytes

    def __repr__(self):
        return f"Enclosure('{self.file_name}')"


class Episode:
    def __init__(self, title, link, description, guid, duration, enclosure, pubDate, image=None):
        
        self.title = title
        self.link = link
        self.description = description
        self.guid = guid
        self.duration = duration # Integer, measure seconds
        self.enclosure = enclosure
        self.pubDate = pubDate
        self.image = image

    def __iter__(self):
        return \
            iter([
                ("title", self.title),
                ("link", self.link),
                ("description", self.description),
                ("guid", self.guid),
                ("duration", self.duration),
                ("pubDate", self.pubDate.isoformat()),
                ("image", self.image),

                ("file_name", self.enclosure.file_name),
                ("audio_format", self.enclosure.audio_format.value),
                ("length", self.enclosure.length)
                ])

    def __repr__(self):
        return f"Episode('{self.title}', '{self.link}', '{self.guid}' ...)"
