# -*- coding: utf-8 -*-

import json
from pathlib import Path

import opp.podcast as podcast
import opp.visitor as visitor
import opp.administrator as adm


class AdminDS(adm.PodcastDatastore):

    """Provide a dependency inversion layer so that arbitrary data-storage backends can be made compatible with the administrator's use-cases."""

    def __init__(self, data_path):
        self._data_path = data_path

    def initialize_channel(self, title, link, description, image, author, email, language, category, explicit, keywords):
        """Initialize a new channel."""

        channel_data = \
            { "channel":
                    { "title": title,
                    "link": link,
                    "description": description,
                    "image": image,
                    "author": author,
                    "email": email,
                    "language": language,
                    "category": category,
                    "explicit": explicit,
                    "keywords": keywords
                    }
            }

        with open(self._data_path, "w") as file:
            json.dump(channel_data, file)


    def get_channel(self):
        """Produce the podcast.Channel."""

        with open(self._data_path, "r") as file:
            podcast_data = json.load(file)
            chdata = podcast_data["channel"]

        channel = podcast.Channel(chdata["title"], chdata["link"], chdata["description"], chdata["image"], chdata["author"], chdata["email"], chdata["language"], chdata["category"], chdata["explicit"], chdata["keywords"])

        return channel


    def update_channel(self, title, link, description, image, author, email, language, category, explicit, keywords):
        """Update the externally stored podcast channel information."""

        with open(self._data_path, "r") as file:
            podcast_data = json.load(file)

        chdata = {  "title": title,
                    "link": link,
                    "description": description,
                    "image": image,
                    "author": author,
                    "email": email,
                    "language": language,
                    "category": category,
                    "explicit": explicit,
                    "keywords": keywords
                    }

        podcast_data["channel"] = chdata

        with open(self._data_path, "w") as file:
            json.dump(podcast_data, file)



    def create_episode(self, title, link, description, guid, duration, pubDate, file_name, audio_format, length, image=None):
        """Save a new episode."""
        pass

    def get_episodes(self):
        """Produce an iterable of podcast.Episodes."""
        pass

    def update_episode(self, guid, title=None, link=None, description=None, duration=None, pubDate=None, file_name=None, audio_format=None, length=None, image=None):
        """Update an existing episode."""
        pass

    def delete_episode(self, guid):
        """Delete an episode.""show " = """
        pass

