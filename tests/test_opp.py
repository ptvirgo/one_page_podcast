#!/usr/bin/env python
# -*- coding: utf-8 -*-

from opp.podcast import Channel, Episode, Enclosure, AudioFormat

import opp.administrator as administrator
import opp.visitor as visitor

import tests.factories as factories


class VisitorTestStore(visitor.PodcastDatastore):

    def __init__(self):
        self.channel = factories.ChannelFactory()
        self.episodes = [ factories.EpisodeFactory(), factories.EpisodeFactory(), factories.EpisodeFactory() ]


    def get_channel(self):
        return self.channel
            

    def get_episodes(self):
        return self.episodes


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

    def create_episode(self, title, link, description, guid, duration, pubDate, file_name, audio_format, length, image=None):
        """Save a new episode."""
        enclosure = Enclosure(file_name, AudioFormat(audio_format), length)
        episode = Episode(title, link, description, guid, duration, enclosure, pubDate, image)

        self._episodes.append(episode)
        self._episodes.sort(key=lambda x: x.pubDate)

    def get_episodes(self):
        """Produce an iterable of podcast.Episodes."""
        return self._episodes

    def update_episode(self, guid, title=None, link=None, description=None, duration=None, pubDate=None, file_name=None, audio_format=None, length=None, image=None):
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

        if pubDate is not None:
            episode.pubDate = pubDate

        if image is not None:
            episode.image = image

        if file_name is not None:
            episode.enclosure.file_name = file_name

        if audio_format is not None:
            episode.enclosure.audio_format = AudioFormat(audio_format)

        if length is not None:
            episode.enclosure.length = length

    def delete_episode(self, guid):
        """Delete an episode."""

        self._episodes = [ ep for ep in self._episodes if ep.guid != guid ]


class TestAdministrator:

    def test_initialize_channel(self):
        datastore = AdministratorTestStore()
        datastore._channel = None

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

    def test_create_episode(self):
        datastore = AdministratorTestStore(2)
        admin_interface = administrator.AdminPodcast(datastore)
        new = factories.EpisodeFactory()

        admin_interface.create_episode(new.title, new.link, new.description, new.guid, new.duration, new.pubDate, new.enclosure.file_name, new.enclosure.audio_format.value, new.enclosure.length, image=new.image)

        result = None

        for episode in datastore._episodes:
            if episode.guid == new.guid:
                result = episode

        assert dict(result) == dict(new)

    def test_update_episode(self):
        datastore = AdministratorTestStore(3)
        admin_interface = administrator.AdminPodcast(datastore)

        prev = datastore._episodes[1]
        new = factories.EpisodeFactory()

        admin_interface.update_episode(prev.guid, title=new.title)
        assert prev.title == new.title

        admin_interface.update_episode(prev.guid, link=new.link)
        assert prev.link == new.link

        admin_interface.update_episode(prev.guid, description=new.description)
        assert prev.description == new.description

        admin_interface.update_episode(prev.guid, duration=new.duration)
        assert prev.duration == new.duration

        admin_interface.update_episode(prev.guid, pubDate=new.pubDate.isoformat())
        assert prev.pubDate == new.pubDate

        admin_interface.update_episode(prev.guid, image=new.image)
        assert prev.image == new.image

        admin_interface.update_episode(prev.guid, file_name=new.enclosure.file_name)
        assert prev.enclosure.file_name == new.enclosure.file_name

        admin_interface.update_episode(prev.guid, audio_format=new.enclosure.audio_format.value)
        assert prev.enclosure.audio_format == new.enclosure.audio_format

        admin_interface.update_episode(prev.guid, length=new.enclosure.length)
        assert prev.enclosure.length == new.enclosure.length


    def test_delete_episode(self):
        datastore = AdministratorTestStore(3)
        admin_interface = administrator.AdminPodcast(datastore)

        guid = datastore._episodes[1].guid
        admin_interface.delete_episode(guid)

        for episode in datastore._episodes:
            assert episode.guid != guid
