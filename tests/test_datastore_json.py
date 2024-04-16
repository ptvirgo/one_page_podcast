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
