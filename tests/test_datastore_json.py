#!/usr/bin/env python
# -*- coding: utf-8 -*-

import opp.datastore.json_file as jsf
import tests.factories as factories

# write a test of AdminDS features.


class TestAdminDS:
    """Test the AdminDS features."""

    def test_initialize_channel(self, tmp_path):
        """Make sure we can initialize and retrieve the channel."""

        channel = factories.ChannelFactory()
        datastore = jsf.AdminDS(tmp_path / "test_initialize_channel.js")

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

    def test_update_channel(self, tmp_path):
        """Make sure we can update the channel."""

        datastore = jsf.AdminDS(tmp_path / "test_update_channel.js")
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

    def test_create_episode(self, tmp_path):
        """Make sure we can create and retrieve episodes."""

        datastore = jsf.AdminDS(tmp_path / "test_create_epsiode.js")

        channel = factories.ChannelFactory()
        datastore.initialize_channel(channel.title, channel.link, channel.description, channel.image, channel.author, channel.email, channel.language, channel.category, channel.explicit, channel.keywords)

        first = factories.EpisodeFactory()

        datastore.create_episode(first.title, first.link, first.description, str(first.guid), first.duration, first.pubDate.isoformat(), first.enclosure.file_name, first.enclosure.audio_format.value, first.enclosure.length, first.image)

        result = datastore.get_episodes()[0]
        self.check_episode(result, first)

        second = factories.EpisodeFactory()
        third = factories.EpisodeFactory()

        datastore.create_episode(second.title, second.link, second.description, str(second.guid), second.duration, second.pubDate.isoformat(), second.enclosure.file_name, second.enclosure.audio_format.value, second.enclosure.length, second.image)
        datastore.create_episode(third.title, third.link, third.description, str(third.guid), third.duration, third.pubDate.isoformat(), third.enclosure.file_name, third.enclosure.audio_format.value, third.enclosure.length, third.image)

        triple = sorted([first, second, third], key=lambda x: x.pubDate, reverse=True)
        result = datastore.get_episodes()

        for i in range(3):
            self.check_episode(result[i], triple[i])

        # WIP:  You'll probably need to discard support for the "image" temporarily, and re-evaluate whether the audio file is passed as a path or a datastream during the create & update phase.

    @staticmethod
    def check_episode(result, expect):
        """Verify that two episodes are effectively identical."""

        assert result.title == expect.title
        assert result.link == expect.link
        assert result.description == expect.description
        assert result.guid == expect.guid
        assert result.duration == expect.duration
        assert result.pubDate == expect.pubDate
        assert result.enclosure.file_name == expect.enclosure.file_name
        assert result.enclosure.audio_format == expect.enclosure.audio_format
        assert result.enclosure.length == expect.enclosure.length
        assert result.image == expect.image
