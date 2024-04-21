# -*- coding: utf-8 -*-

from datetime import date
import json
from pathlib import Path
import uuid

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
        ep_data = { "title": title,
                    "link": link,
                    "description": description,
                    "guid": guid,
                    "duration": duration,
                    "pubDate": pubDate,
                    "file_name": file_name,
                    "audio_format": audio_format,
                    "length": length,
                    "image": image
                    }

        with open(self._data_path, "r") as file:
            podcast_data = json.load(file)

        if type(podcast_data.get("episodes")) is list:
            podcast_data["episodes"].append(ep_data)
        else:
            podcast_data["episodes"] = [ep_data]

        podcast_data["episodes"].sort(key=lambda ep: ep["pubDate"], reverse=True)

        with open(self._data_path, "w") as file:
            json.dump(podcast_data, file)


    def get_episodes(self):
        """Produce an iterable of podcast.Episodes."""

        with open(self._data_path, "r") as file:
            podcast_data = json.load(file)

        if "episodes" in podcast_data:
            episode_data = podcast_data["episodes"]
        else:
            episode_data = []

        return [ self.data_to_episode(ep) for ep in episode_data ]


    @staticmethod
    def data_to_episode(ep_data):
        """Convert the JSON data to an Episode object."""
        enclosure = podcast.Enclosure(ep_data["file_name"], podcast.AudioFormat(ep_data["audio_format"]), ep_data["length"])

        episode = podcast.Episode(ep_data["title"], ep_data["link"], ep_data["description"], uuid.UUID(ep_data["guid"]), ep_data["duration"], enclosure, date.fromisoformat(ep_data["pubDate"]))
        return episode

    def update_episode(self, guid, title=None, link=None, description=None, duration=None, pubDate=None, file_name=None, audio_format=None, length=None, image=None):
        """Update an existing episode."""
        pass

    def delete_episode(self, guid):
        """Delete an episode.""show " = """
        pass
