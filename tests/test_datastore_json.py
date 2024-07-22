#!/usr/bin/env python
# -*- coding: utf-8 -*-

import opp.datastore.json_file as jsf
from opp.podcast import AudioFormat, Channel, Episode

import pytest
from pathlib import Path


import tests.factories as factories
from uuid import UUID

data_dir = Path(__file__).parent / "data"

# write a test of AdminDS features.


# Fixtures

def audio_file(audio_format):

    if audio_format == AudioFormat.OggOpus:
        return data_dir / "speech_16.opus"

    if audio_format == AudioFormat.OggVorbis:
        return data_dir / "speech.ogg"

    return data_dir / "speech_32.mp3"


def initialize_datastore(ds, episodes=3):
    channel = factories.ChannelFactory()
    ds.initialize_channel(channel.title, channel.link, channel.description, channel.image, channel.author, channel.email, channel.language, channel.category, channel.explicit, channel.keywords)

    for i in range(episodes):
        ep = factories.EpisodeFactory()

        with open(audio_file(ep.audio_format), "rb") as file:
            ds.create_episode(file, ep.title, ep.description, str(ep.guid), ep.duration, ep.publication_date, ep.audio_format.value)


@pytest.fixture
def datastore(tmp_path):

    def make_datastore(initialize=True, episodes=3):
        ds_dir = Path(tmp_path)
        ds = jsf.AdminDS(ds_dir)

        if initialize:
            initialize_datastore(ds, episodes=episodes)

        return ds

    return make_datastore


@pytest.fixture
def visitor_ds(tmp_path):

    ds_dir = Path(tmp_path)
    admin_ds = jsf.AdminDS(ds_dir)

    initialize_datastore(admin_ds, episodes=3)

    return jsf.VisitorDS(ds_dir)


# Tests

class TestVisitorDS:
    """Test the VisitorDS features."""

    def test_get_channel(self, visitor_ds):
        channel = visitor_ds.get_channel()

        assert type(channel) is Channel

    def test_get_episodes(self, visitor_ds):
        episodes = visitor_ds.get_episodes()
        assert len(episodes) == 3

        for ep in episodes:
            assert type(ep) is Episode


class TestAdminDS:
    """Test the AdminDS features."""

    def test_initialize_channel(self, datastore):
        """Make sure we can initialize and retrieve the channel."""

        channel = factories.ChannelFactory()

        ds = datastore(initialize=False)
        ds.initialize_channel(channel.title, channel.link, channel.description, channel.image, channel.author, channel.email, channel.language, channel.category, channel.explicit, channel.keywords)

        result = ds.get_channel()

        assert result.title == channel.title
        assert result.link == channel.link
        assert result.description == channel.description
        assert result.image == channel.image
        assert result.author == channel.author
        assert result.email == channel.email
        assert result.language == channel.language
        assert result.category == channel.category
        assert result.explicit == channel.explicit
        assert result.keywords == channel.keywords

    def test_update_channel(self, datastore):
        """Make sure we can update the channel."""
        fst = factories.ChannelFactory()
        snd = factories.ChannelFactory()

        ds = datastore(initialize=False)

        ds.initialize_channel(fst.title, fst.link, fst.description, fst.image, fst.author, fst.email, fst.language, fst.category, fst.explicit, fst.keywords)
        ds.update_channel(snd.title, snd.link, snd.description, snd.image, snd.author, snd.email, snd.language, snd.category, snd.explicit, snd.keywords)

        result = ds.get_channel()

        assert result.title == snd.title
        assert result.link == snd.link
        assert result.description == snd.description
        assert result.image == snd.image
        assert result.author == snd.author
        assert result.email == snd.email
        assert result.language == snd.language
        assert result.category == snd.category
        assert result.explicit == snd.explicit
        assert result.keywords == snd.keywords

    def test_file_path(self, datastore):
        """Make sure the datastore file path is sane."""

        ds = datastore(False)
        test_id = UUID('eb8766d0-ea67-4de4-bdb5-ef279fe7efb4')

        opus_path = ds.audio_file_path(test_id, AudioFormat.OggOpus.value)
        assert opus_path.name == "eb8766d0-ea67-4de4-bdb5-ef279fe7efb4.opus"

        vorbis_path = ds.audio_file_path(test_id, AudioFormat.OggVorbis.value)
        assert vorbis_path.name == "eb8766d0-ea67-4de4-bdb5-ef279fe7efb4.ogg"

        mp3_path = ds.audio_file_path(test_id, AudioFormat.MP3.value)
        assert mp3_path.name == "eb8766d0-ea67-4de4-bdb5-ef279fe7efb4.mp3"

    def test_create_episode(self, datastore):
        """Make sure we can create and retrieve episodes."""
        ds = datastore(initialize=True, episodes=0)

        episodes = []

        for i in range(3):
            ep = factories.EpisodeFactory()
            episodes.append(ep)

            with open(audio_file(ep.audio_format), "rb") as file:
                ds.create_episode(file, ep.title, ep.description, str(ep.guid), ep.duration, ep.publication_date, ep.audio_format.value)

        episodes.sort(key=lambda ep: ep.publication_date, reverse=True)
        results = ds.get_episodes()

        for i in range(3):
            assert results[i] == episodes[i]
            audio_file_path = ds.audio_file_path(results[i].guid, results[i].audio_format)

            assert audio_file_path.exists()
            assert not audio_file_path.is_dir()

    def test_update_episode(self, datastore):
        """Make sure we can update an episode."""

        ds = datastore()
        episodes = ds.get_episodes()

        control_prior = episodes[0]
        old = episodes[1]

        new = factories.EpisodeFactory()

        for attribute in ["title", "description", "duration", "publication_date"]:
            value = getattr(new, attribute)
            ds.update_episode(str(old.guid), **{attribute: value})
            updated = ds.get_episodes()[1]

            assert getattr(updated, attribute) == value

        control_post = ds.get_episodes()[0]
        assert control_post == control_prior

    def test_delete_episode(self, datastore):
        """Make sure we can delete an episode."""

        ds = datastore()

        prior_episodes = ds.get_episodes()
        ds.delete_episode(str(prior_episodes[1].guid))

        post_episodes = ds.get_episodes()

        assert len(post_episodes) == 2

        assert post_episodes[0] == prior_episodes[0]
        assert post_episodes[-1] == prior_episodes[-1]
