#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import pytest
from uuid import UUID

from opp.podcast import Channel, Episode, AudioFormat, audio_extension

import opp.administrator as administrator
import opp.visitor as visitor

import tests.factories as factories


data_dir = Path(__file__).parent / "data"


class VisitorTestStore(visitor.PodcastDatastore):

    def __init__(self, channel, episodes):
        self.channel = channel
        self.episodes = sorted(episodes, key=lambda ep: ep.publication_date)

    def get_channel(self):
        return self.channel

    def get_episodes(self):
        return self.episodes


@pytest.fixture
def visitor_store():
    channel = factories.ChannelFactory()
    episodes = [factories.EpisodeFactory(), factories.EpisodeFactory(), factories.EpisodeFactory()]
    return VisitorTestStore(channel, episodes)


class TestVisitor:

    def test_visit(self, visitor_store):
        vp = visitor.VisitPodcast(visitor_store)

        result = vp.podcast_data()

        assert result["channel"]["title"] == visitor_store.channel.title
        assert result["channel"]["link"] == visitor_store.channel.link
        assert result["channel"]["description"] == visitor_store.channel.description
        assert result["channel"]["image"] == visitor_store.channel.image
        assert result["channel"]["author"] == visitor_store.channel.author
        assert result["channel"]["email"] == visitor_store.channel.email
        assert result["channel"]["language"] == visitor_store.channel.language
        assert result["channel"]["category"] == visitor_store.channel.category
        assert result["channel"]["explicit"] == visitor_store.channel.explicit
        assert result["channel"]["keywords"] == visitor_store.channel.keywords

        episode = visitor_store.episodes[0]
        episode_result = result["episodes"][0]

        assert episode_result["title"] == episode.title
        assert episode_result["description"] == episode.description
        assert episode_result["guid"] == str(episode.guid)
        assert episode_result["duration"] == episode.duration
        assert episode_result["publication_date"] == episode.publication_date.isoformat()
        assert episode_result["audio_format"] == episode.audio_format.value

        assert len(result["episodes"]) == len(visitor_store.episodes)


class AdministratorTestStore(administrator.PodcastDatastore):

    def __init__(self, data_dir):
        self._channel = None
        self._episodes = []
        self._episode_dir = data_dir / "episodes/"

    def initialize_channel(self, title, link, description, image, author, email, language, category, explicit, keywords):
        self._channel = Channel(title=title, link=link, description=description, image=image, author=author, email=email, language=language, category=category, explicit=explicit, keywords=keywords)

    def get_channel(self):
        """Produce the podcast.Channel."""
        return self._channel

    def update_channel(self, title=None, link=None, description=None, image=None, author=None, email=None, language=None, category=None, explicit=None, keywords=None):
        """Update the externally stored podcast channel information."""

        if type(title) is str:
            self._channel.title = title

        if type(link) is str:
            self._channel.link = link

        if type(description) is str:
            self._channel.description = description

        if type(image) is str:
            self._channel.image = image

        if type(author) is str:
            self._channel.author = author

        if type(email) is str:
            self._channel.email = email

        if type(language) is str:
            self._channel.language = language

        if type(category) is str:
            self._channel.category = category

        if type(explicit) is bool:
            self._channel.explicit = explicit

        if type(keywords) is list:
            self._channel.keywords = keywords

    def create_episode(self, file_handle, title, description, guid, duration, publication_date, audio_format):
        """Save a new episode."""

        ep_path = self.audio_file_path(guid, audio_format)
        episode = Episode(title, description, UUID(guid), duration, publication_date, AudioFormat(audio_format), ep_path)

        self._episodes.append(episode)
        self._episodes.sort(key=lambda x: x.publication_date)

    def get_episodes(self):
        """Produce an iterable of podcast.Episodes."""
        return self._episodes

    def update_episode(self, guid, title=None, description=None, duration=None, publication_date=None):
        """Update an existing episode."""

        guids = [ep.guid for ep in self._episodes]
        select = guids.index(guid)
        episode = self._episodes[select]

        if title is not None:
            episode.title = title

        if description is not None:
            episode.description = description

        if duration is not None:
            episode.duration = duration

        if publication_date is not None:
            episode.publication_date = publication_date

    def delete_episode(self, guid):
        """Delete an episode."""

        self._episodes = [ep for ep in self._episodes if ep.guid != guid]

    def audio_file_path(self, guid, audio_format):
        """Produce the path name for an episode."""
        ext = audio_extension(audio_format)
        return self._episode_dir / f"{guid}.{ext}"


def make_admin_datastore(path, initialize=True, episode_count=0):
    ds = AdministratorTestStore(path)

    if initialize:
        channel = factories.ChannelFactory()
        ds.initialize_channel(channel.title, channel.link, channel.description, channel.image, channel.author, channel.email, channel.language, channel.category, channel.explicit, channel.keywords)

        for i in range(episode_count):
            ep = factories.EpisodeFactory()
            ds.create_episode(None, ep.title, ep.description, str(ep.guid), ep.duration, ep.publication_date, ep.audio_format.value)

    return ds


@pytest.fixture
def admin_store(tmp_path):

    def wrapped(*args, **kwargs):
        return make_admin_datastore(tmp_path, *args, **kwargs)

    return wrapped


@pytest.fixture
def admin_interface(tmp_path):
    datastore = make_admin_datastore(tmp_path)
    admin_interface = administrator.AdminPodcast(datastore)

    yield admin_interface


class TestAdministrator:

    def test_initialize_channel(self, admin_store):
        datastore = admin_store(initialize=False)

        expect = factories.ChannelFactory()
        admin_interface = administrator.AdminPodcast(datastore)

        admin_interface.initialize_channel(expect.title, expect.link, expect.description, expect.image, expect.author, expect.email, expect.language, expect.category, expect.explicit, expect.keywords)

        result = admin_interface.get_channel()

        assert result["title"] == expect.title
        assert result["link"] == expect.link
        assert result["description"] == expect.description
        assert result["image"] == expect.image
        assert result["author"] == expect.author
        assert result["email"] == expect.email
        assert result["language"] == expect.language
        assert result["category"] == expect.category
        assert result["explicit"] == expect.explicit
        assert result["keywords"] == expect.keywords

    def test_get_channel(self, admin_store):
        datastore = admin_store()
        admin_interface = administrator.AdminPodcast(datastore)

        result = admin_interface.get_channel()
        expect = datastore._channel

        assert result["title"] == expect.title
        assert result["link"] == expect.link
        assert result["description"] == expect.description
        assert result["image"] == expect.image
        assert result["author"] == expect.author
        assert result["email"] == expect.email
        assert result["language"] == expect.language
        assert result["category"] == expect.category
        assert result["explicit"] == expect.explicit
        assert result["keywords"] == expect.keywords

    def test_get_episodes(self, admin_store):
        count = 3
        datastore = admin_store(episode_count=count)
        admin_interface = administrator.AdminPodcast(datastore)

        results = admin_interface.get_episodes()
        expects = datastore._episodes

        def check_episode(check, expect):
            assert check["title"] == expect.title
            assert check["description"] == expect.description
            assert check["guid"] == str(expect.guid)
            assert check["duration"] == expect.duration
            assert check["publication_date"] == expect.publication_date.isoformat()
            assert check["audio_format"] == expect.audio_format.value

        for i in range(count):
            check_episode(results[i], expects[i])

    def test_update_channel(self, admin_interface):
        new = factories.ChannelFactory()

        admin_interface.update_channel(title=new.title, link=new.link, description=new.description, image=new.image, author=new.author, email=new.email, language=new.language, category=new.category, explicit=new.explicit, keywords=new.keywords)
        result = admin_interface.get_channel()

        assert result["title"] == new.title
        assert result["link"] == new.link
        assert result["description"] == new.description
        assert result["image"] == new.image
        assert result["author"] == new.author
        assert result["email"] == new.email
        assert result["language"] == new.language
        assert result["category"] == new.category
        assert result["explicit"] == new.explicit
        assert result["keywords"] == new.keywords

    def test_create_episode(self, admin_store):
        datastore = admin_store(episode_count=2)
        admin_interface = administrator.AdminPodcast(datastore)
        new = factories.EpisodeFactory()

        guid = admin_interface.create_episode(None, new.title, new.description, new.duration, new.publication_date, new.audio_format.value)

        guids = [str(ep.guid) for ep in datastore._episodes]
        select = guids.index(guid)

        result = dict(datastore._episodes[select])
        result.pop("guid")
        result.pop("path")

        expect = dict(new)
        expect.pop("guid")
        expect.pop("path")

        assert result == expect

    def test_update_episode(self, admin_store):
        datastore = admin_store(episode_count=3)
        admin_interface = administrator.AdminPodcast(datastore)

        prev = datastore._episodes[1]
        new = factories.EpisodeFactory()

        admin_interface.update_episode(prev.guid, title=new.title)
        assert prev.title == new.title

        admin_interface.update_episode(prev.guid, description=new.description)
        assert prev.description == new.description

        admin_interface.update_episode(prev.guid, duration=new.duration)
        assert prev.duration == new.duration

        admin_interface.update_episode(prev.guid, publication_date=new.publication_date)
        assert prev.publication_date == new.publication_date

    def test_delete_episode(self, admin_store):
        datastore = admin_store(episode_count=3)
        admin_interface = administrator.AdminPodcast(datastore)

        guid = datastore._episodes[1].guid
        admin_interface.delete_episode(guid)

        for episode in datastore._episodes:
            assert episode.guid != guid

    def test_extract_details(self, admin_store):
        datastore = admin_store()
        admin_interface = administrator.AdminPodcast(datastore)

        with open(data_dir / "speech.ogg", "rb") as file:
            result = admin_interface.extract_details(file)

        assert result["duration"] == 11
        assert result["length"] == 95837
        assert result["audio_format"] == AudioFormat.OggVorbis.value
        assert result["title"] == "Speech Test at q3"
        assert result["description"] == "I can haz Vorbis?"

        with open(data_dir / "speech_16.opus", "rb") as file:
            result = admin_interface.extract_details(file)

        assert result["duration"] == 11
        assert result["length"] == 22521
        assert result["audio_format"] == AudioFormat.OggOpus.value
        assert result["title"] == "Speech Test at 16k"
        assert result["description"] == "I can haz Opus?"

        with open(data_dir / "speech_32.mp3", "rb") as file:
            result = admin_interface.extract_details(file)

        assert result["duration"] == 11
        assert result["length"] == 44858
        assert result["audio_format"] == AudioFormat.MP3.value
        assert result["title"] == "Speech Test at 32k"
        assert result["description"] == "I can haz MP3?"
