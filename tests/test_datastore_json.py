#!/usr/bin/env python
# -*- coding: utf-8 -*-

import opp.datastore.json_file as jsf
import tests.factories as factories

# write a test of AdminDS features.

class TestAdminDS:
    """Test the AdminDS features."""

    def test_initialize_channel(self, tmp_path):
        "Make sure we can initialize and retrieve the channel."""

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
