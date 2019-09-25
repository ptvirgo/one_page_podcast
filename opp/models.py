# -*- coding: utf-8 -*-
from cleantext import clean
import enum

from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

db = SQLAlchemy()
episode_keywords = db.Table(
    "episode_keywords",
    db.Column("episode_id", db.Integer, db.ForeignKey("episode.item_id"),
              primary_key=True),
    db.Column("keyword_id", db.Integer, db.ForeignKey("keyword.item_id"),
              primary_key=True))


class Episode(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    published = db.Column(db.DateTime, nullable=False, index=True)
    description = db.Column(db.String(4096), nullable=False)
    image = db.Column(db.String(256))
    explicit = db.Column(db.Boolean, default=False, nullable=False)

    keywords = db.relationship("Keyword", backref="episodes",
                               secondary=episode_keywords)

    def set_keywords(self, words):
        """Replace self.keywords with newly provided words"""
        for kw in list(self.keywords):
            self.keywords.remove(kw)

        for word in words:
            word = word.strip()
            kw = Keyword.query.filter_by(word=word).first()

            if kw is None:
                kw = Keyword(word=word)

            self.keywords.append(kw)

    def __repr__(self):
        return "<Episode %s, %s>" % (self.published.isoformat(), self.title)

    def __iter__(self):
        """Produce iterable of attributes"""
        return iter([
            ("item_id", self.item_id),
            ("title", self.title),
            ("published", self.published.isoformat()),
            ("description", self.description),
            ("image", getattr(self, "image", None)),
            ("explicit", self.explicit),
            ("audio_file", dict(self.audio_file)),
            ("keywords", [kw.word for kw in self.keywords])])


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


class AudioFile(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(256), unique=True, index=True)
    audio_format = db.Column(db.Enum(AudioFormat))
    length = db.Column(db.Integer)
    duration = db.Column(db.Integer)
    episode_id = db.Column(
        db.Integer, db.ForeignKey("episode.item_id", ondelete="CASCADE"))
    episode = db.relationship("Episode", backref=db.backref(
        "audio_file", uselist=False, cascade="all, delete-orphan"))

    @staticmethod
    def standardized_name(published, title, file_format):
        """
        Produce a standardized file name that can be used by new AudioFiles
        """
        day = published.strftime("%Y-%m-%d")
        extension = file_format.value
        name = clean(title, no_punct=True).replace(' ', '_')
        return secure_filename("%s-%s.%s" % (day, name, extension))
    
    def __repr__(self):
        return "<AudioFile %s>" % self.file_name

    def __iter__(self):
        """Produce iterable of attributes"""
        return iter([
            ("item_id", self.item_id),
            ("file_name", self.file_name),
            ("audio_format", self.audio_format.value),
            ("length", self.length),
            ("duration", self.duration)])


class Keyword(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(32))

    def __str__(self):
        return self.word

    def __repr__(self):
        return "<Keyword %s>" % self.word
