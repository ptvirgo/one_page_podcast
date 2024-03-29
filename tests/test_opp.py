#!/usr/bin/env python
# -*- coding: utf-8 -*-

from opp.podcast import Episode

import opp.administrator as administrator
import opp.visitor as visitor

import tests.factories as factories


class VisitorTestStore(visitor.PodcastDatastore):

    def __init__(self):
        self.channel = factories.ChannelFactory()
        self.episodes = [ factories.EpisodeFactory(), factories.EpisodeFactory(), factories.EpisodeFactory() ]


    def get_channel(self):
        return self.channel.as_dict()
            

    def get_episodes(self):
        return [ ep.as_dict() for ep in self.episodes ]


class TestVisitor:

    def test_visit(self):
        loader = VisitorTestStore()
        vp = visitor.VisitPodcast(loader)

        result = vp.podcast_data()

        assert result["channel"]["title"] == loader.channel.title
        assert result["channel"]["link"] == loader.channel.link
        assert result["channel"]["description"] == loader.channel.description
        assert result["channel"]["image"] == loader.channel.image
        assert result["channel"]["author"] == loader.channel.author
        assert result["channel"]["email"] == loader.channel.email
        assert result["channel"]["language"] == loader.channel.language
        assert result["channel"]["category"] == loader.channel.category
        assert result["channel"]["explicit"] == loader.channel.explicit
        assert result["channel"]["keywords"] == loader.channel.keywords

        episode = loader.episodes[0]
        episode_result = result["episodes"][0]

        assert episode_result["title"] == episode.title
        assert episode_result["link"] == episode.link
        assert episode_result["description"] == episode.description
        assert episode_result["guid"] == episode.guid
        assert episode_result["duration"] == episode.duration
        assert episode_result["pubDate"] == episode.pubDate.isoformat()
        assert episode_result["image"] == episode.image

        assert episode_result["file_name"] == episode.enclosure.file_name
        assert episode_result["audio_format"] == episode.enclosure.audio_format.value
        assert episode_result["length"] == episode.enclosure.length

        assert len(result["episodes"]) == len(loader.episodes)


class AdministratorTestStore(administrator.PodcastDatastore):

    def __init__(self, make_episodes=0):
        self._channel = factories.ChannelFactory()
        self._episodes = []

        for i in range(make_episodes):
            self._episodes.append(factories.EpisodeFactory())

        self._episodes.sort(key=lambda ep: ep.pubDate)

    def get_channel(self):
        """Produce the podcast.Channel."""
        return self._channel.as_dict()


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


    def create_episode(self, title, link, description, guid, duration, enclosure, pubDate, image=None):
        """Save a new episode."""
        episode = Episode(title, link, description, guid, duration, enclosure, pubDate, image)
        self._episodes.append(episode)
        self._episodes.sort(key=lambda x: x.pubDate)


    def get_episodes(self):
        """Produce an iterable of podcast.Episodes."""
        return [ ep.as_dict() for ep in self._episodes ]


    def update_episode(self, guid, title=None, link=None, description=None, duration=None, enclosure=None, pubDate=None, image=None):
        """Update an existing episode."""

        episode = None

        for ep in self._episodes:
            if ep.guid == guid:
                episode = ep

        if episode is None:
            raise ValueError("Invalid GUID")

        if title is not None:
            episode.title = title

        if link is not None:
            episode.link = link

        if description is not None:
            episode.description = description

        if duration is not None:
            episode.duration = duration

        if enclosure is not None:
            episode.enclosure = enclosure

        if pubDate is not None:
            episode.pubDate = pubDate

        if image is not None:
            episode.image = image


    def delete_episode(self, guid):
        """Delete an episode."""

        self._episodes = [ ep for ep in self._episodes if ep.guid != guid ]


class TestAdministrator:

    def test_get_channel(self):
        datastore = AdministratorTestStore()
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

    def test_get_episodes(self):
        count = 3
        datastore = AdministratorTestStore(make_episodes=count)
        admin_interface = administrator.AdminPodcast(datastore)

        results = admin_interface.get_episodes()
        expects = datastore._episodes

        def check_episode(check, expect):
            assert check["title"] == expect.title
            assert check["link"] == expect.link
            assert check["description"] == expect.description
            assert check["guid"] == expect.guid
            assert check["duration"] == expect.duration
            assert check["pubDate"] == expect.pubDate.isoformat()
            assert check["image"] == expect.image
            assert check["file_name"] == expect.enclosure.file_name
            assert check["audio_format"] == expect.enclosure.audio_format.value

        for i in range(count):
            check_episode(results[i], expects[i])

    def test_update_channel(self):
        datastore = AdministratorTestStore()
        admin_interface = administrator.AdminPodcast(datastore)
        new = factories.ChannelFactory()

        admin_interface.update_channel(title=new.title, link=new.link, description=new.description, image=new.image, author=new.author, email=new.email, language=new.language, category=new.category, explicit=new.explicit, keywords=new.keywords)
        result = admin_interface.get_channel()

        assert result["title"] == new.title
        assert result["link"] ==new.link
        assert result["description"] == new.description
        assert result["image"] == new.image
        assert result["author"] == new.author
        assert result["email"] == new.email
        assert result["language"] == new.language
        assert result["category"] == new.category
        assert result["explicit"] == new.explicit
        assert result["keywords"] == new.keywords
