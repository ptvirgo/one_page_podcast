#!/usr/bin/env python
# -*- coding: utf-8 -*-

import opp.datastore.json_file as jsf

import pytest
from pathlib import Path
import tests.factories as factories


# write a test of AdminDS features.


class TestAdminDS:
    """Test the AdminDS features."""

    @pytest.fixture
    def datastore(self, tmp_path):
        ds_dir = Path(tmp_path)
        ds = jsf.AdminDS(ds_dir)
        yield ds

    def test_initialize_channel(self, datastore):
        """Make sure we can initialize and retrieve the channel."""

        channel = factories.ChannelFactory()

        datastore.initialize_channel(channel.title, channel.link, channel.description, channel.image, channel.author, channel.email, channel.language, channel.category, channel.explicit, channel.keywords)

        result = datastore.get_channel()

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

        datastore.initialize_channel(fst.title, fst.link, fst.description, fst.image, fst.author, fst.email, fst.language, fst.category, fst.explicit, fst.keywords)
        datastore.update_channel(snd.title, snd.link, snd.description, snd.image, snd.author, snd.email, snd.language, snd.category, snd.explicit, snd.keywords)

        result = datastore.get_channel()

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

    def test_create_episode(self, datastore):
        """Make sure we can create and retrieve episodes."""

        channel = factories.ChannelFactory()
        datastore.initialize_channel(channel.title, channel.link, channel.description, channel.image, channel.author, channel.email, channel.language, channel.category, channel.explicit, channel.keywords)

        episodes = []

        for i in range(3):
            ep = factories.EpisodeFactory()
            episodes.append(ep)
            datastore.create_episode(ep.title, ep.description, str(ep.guid), ep.duration, ep.publication_date, ep.audio_format.value)

        episodes.sort(key=lambda ep: ep.publication_date, reverse=True)
        results = datastore.get_episodes()

        for i in range(3):
            assert results[i] == episodes[i]

    def test_update_episode(self, datastore):
        """Make sure we can update an episode."""

        channel = factories.ChannelFactory()
        datastore.initialize_channel(channel.title, channel.link, channel.description, channel.image, channel.author, channel.email, channel.language, channel.category, channel.explicit, channel.keywords)

        for i in range(3):
            ep = factories.EpisodeFactory()
            datastore.create_episode(ep.title, ep.description, str(ep.guid), ep.duration, ep.publication_date, ep.audio_format.value)

        episodes = datastore.get_episodes()

        control_prior = episodes[0]
        old = episodes[1]

        new = factories.EpisodeFactory()

        for attribute in ["title", "description", "duration", "publication_date"]:
            value = getattr(new, attribute)
            datastore.update_episode(str(old.guid), **{attribute: value})
            updated = datastore.get_episodes()[1]

            assert getattr(updated, attribute) == value

        datastore.update_episode(str(old.guid), audio_format=new.audio_format.value)
        updated = datastore.get_episodes()[1]
        assert updated.audio_format == new.audio_format

        control_post = datastore.get_episodes()[0]
        assert control_post == control_prior

    def test_delete_episode(self, datastore):
        """Make sure we can delete an episode."""

        channel = factories.ChannelFactory()
        datastore.initialize_channel(channel.title, channel.link, channel.description, channel.image, channel.author, channel.email, channel.language, channel.category, channel.explicit, channel.keywords)

        for i in range(3):
            ep = factories.EpisodeFactory()
            datastore.create_episode(ep.title, ep.description, str(ep.guid), ep.duration, ep.publication_date, ep.audio_format.value)

        prior_episodes = datastore.get_episodes()
        datastore.delete_episode(str(prior_episodes[1].guid))

        post_episodes = datastore.get_episodes()

        assert len(post_episodes) == 2

        assert post_episodes[0] == prior_episodes[0]
        assert post_episodes[-1] == prior_episodes[-1]
