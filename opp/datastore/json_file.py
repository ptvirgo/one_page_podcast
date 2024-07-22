# -*- coding: utf-8 -*-

from datetime import date
import json
import uuid

import opp.podcast as podcast
import opp.visitor as visitor
import opp.administrator as adm


opp_json = "opp.json"


def data_to_episode(ep_data):
    """Convert the JSON data to an Episode object."""

    episode = podcast.Episode(ep_data["title"], ep_data["description"], uuid.UUID(ep_data["guid"]), ep_data["duration"], date.fromisoformat(ep_data["publication_date"]), podcast.AudioFormat(ep_data["audio_format"]))
    return episode


class VisitorDS(visitor.PodcastDatastore):

    """Provide a visitor Datastore using a JSON file backend."""

    def __init__(self, data_dir):

        with open(data_dir / opp_json, "r") as file:
            podcast_data = json.load(file)

        channel_data = podcast_data["channel"]
        self._channel = podcast.Channel(channel_data["title"], channel_data["link"], channel_data["description"], channel_data["image"], channel_data["author"], channel_data["email"], channel_data["language"], channel_data["category"], channel_data["explicit"], channel_data["keywords"])

        episode_data = podcast_data["episodes"]
        self._episodes = [data_to_episode(ep) for ep in episode_data]

    def get_channel(self):
        return self._channel

    def get_episodes(self):
        return self._episodes


class AdminDS(adm.PodcastDatastore):

    """Provide an Administrator Datastore using a JSON file backend."""

    def __init__(self, data_dir):
        self._data_dir = data_dir
        self._opp_json = self._data_dir / opp_json

    def initialize_channel(self, title, link, description, image, author, email, language, category, explicit, keywords):
        """Initialize a new channel."""

        channel_data = {
            "channel":
            {
                "title": title,
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

        with open(self._opp_json, "w") as file:
            json.dump(channel_data, file)

    def get_channel(self):
        """Produce the podcast.Channel."""

        with open(self._opp_json, "r") as file:
            podcast_data = json.load(file)
            chdata = podcast_data["channel"]

        channel = podcast.Channel(chdata["title"], chdata["link"], chdata["description"], chdata["image"], chdata["author"], chdata["email"], chdata["language"], chdata["category"], chdata["explicit"], chdata["keywords"])

        return channel

    def update_channel(self, title, link, description, image, author, email, language, category, explicit, keywords):
        """Update the externally stored podcast channel information."""

        with open(self._opp_json, "r") as file:
            podcast_data = json.load(file)

        chdata = {
            "title": title,
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

        with open(self._opp_json, "w") as file:
            json.dump(podcast_data, file)

    def create_episode(self, input_file_handle, title, description, guid, duration, publication_date, audio_format):
        """Save a new episode."""

        audio_file_path = self.audio_file_path(guid, audio_format)

        with open(audio_file_path, "wb") as file:
            file.write(input_file_handle.read())

        ep_data = {
            "title": title,
            "description": description,
            "guid": guid,
            "duration": duration,
            "publication_date": publication_date.isoformat(),
            "audio_format": audio_format,
        }

        with open(self._opp_json, "r") as file:
            podcast_data = json.load(file)

        if type(podcast_data.get("episodes")) is list:
            podcast_data["episodes"].append(ep_data)
        else:
            podcast_data["episodes"] = [ep_data]

        podcast_data["episodes"].sort(key=lambda ep: ep["publication_date"], reverse=True)

        with open(self._opp_json, "w") as file:
            json.dump(podcast_data, file)

    def audio_file_path(self, guid, audio_format):
        """Produce the path name for an episode."""
        ext = podcast.audio_extension(audio_format)
        return self._data_dir / f"{guid}.{ext}"

    def get_episodes(self):
        """Produce an iterable of podcast.Episodes."""

        with open(self._opp_json, "r") as file:
            podcast_data = json.load(file)

        if "episodes" in podcast_data:
            episode_data = podcast_data["episodes"]
        else:
            episode_data = []

        return [data_to_episode(ep) for ep in episode_data]

    def update_episode(self, guid, **kwargs):
        """
        Update an existing episode.

        Required:
            - guid - str, episode global identifier

        Optional:
            - title
            - description
            - duration
            - publication_date

        Return: None
        """

        with open(self._opp_json, "r") as file:
            podcast_data = json.load(file)

        episodes = podcast_data.get("episodes", [])
        guids = [ep["guid"] for ep in episodes]

        select = guids.index(guid)

        for attribute in ["title", "description", "duration"]:

            if kwargs.get(attribute) is not None:
                episodes[select][attribute] = kwargs[attribute]

        if kwargs.get("publication_date") is not None:
            episodes[select]["publication_date"] = kwargs["publication_date"].isoformat()

        podcast_data["episodes"] = episodes

        with open(self._opp_json, "w") as file:
            json.dump(podcast_data, file)

    def delete_episode(self, guid):
        """Delete an episode."""

        with open(self._opp_json, "r") as file:
            podcast_data = json.load(file)

        episodes = podcast_data.get("episodes", [])
        guids = [ep["guid"] for ep in episodes]

        select = guids.index(guid)

        ep = episodes.pop(select)
        ep_path = self.audio_file_path(ep["guid"], ep["audio_format"])
        ep_path.unlink()

        podcast_data["episodes"] = episodes

        with open(self._opp_json, "w") as file:
            json.dump(podcast_data, file)
