#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import opp.administrator as administrator
import opp.datastore.json_file as jsf
from uuid import uuid4

from datetime import date
from pathlib import Path


def make_channel_parser(parser):
    """Produce an argument parser so that a new channel can be initialized."""

    parser.set_defaults(func=initialize_channel)
    parser.add_argument("title", type=str, help="Title")
    parser.add_argument("description", type=str, help="Describe the channel.")
    parser.add_argument("link", type=str, help="URL")
    parser.add_argument("author", type=str, help="Podcast author")
    parser.add_argument("email", type=str, help="Author email")

    parser.add_argument("--category", type=str, help="What kind of podcast is this?", default="news")
    parser.add_argument("--language", type=str, help="Language code. Default 'en'", default="en")
    parser.add_argument("--explicit", action=argparse.BooleanOptionalAction, help="Explicit? Default False", default=False)
    parser.add_argument("--keyword", type=str, nargs="*", action="extend", help="Keyword descriptions of the podcast content.")
    return parser


def initialize_channel(args):
    """Initialize a podcast channel."""
    podcast_admin = admin_interface(args.path)

    podcast_admin.initialize_channel(args.title, args.link, args.description, None, args.author, args.email, args.language, args.category, args.explicit, args.keyword)


def create_episode_parser(parser):
    """Produce a parser that can create a new episode."""
    parser.set_defaults(func=create_episode)
    parser.add_argument("file", type=str, help="Episode file: mp3, ogg vorbis, or opus.")
    parser.add_argument("--title", type=str, help="Title")
    parser.add_argument("--description", type=str, help="Describe the episode.")
    parser.add_argument("--publication-date", type=str, help="Date in YYYY-MM-DD format.")

    return parser


def create_episode(args):
    """Store an episode based on the arguments."""
    podcast_admin = admin_interface(args.path)

    with open(args.file, "rb") as file:
        details = podcast_admin.extract_details(file)

    title = getattr(args, "title") or details["title"]

    if title is None:
        raise ValueError("Missing required title.")

    description = getattr(args, "description") or details["description"]

    if description is None:
        raise ValueError("Missing required description.")

    publication_date_string = getattr(args, "publication_date")

    if publication_date_string is None:
        publication_date = date.today()
    else:
        publication_date = date.fromisoformat(publication_date_string)

    podcast_admin.create_episode(title, description, uuid4(), details["duration"], publication_date, details["audio_format"])


def admin_interface(path_name):
    path = Path(path_name)
    datastore = jsf.AdminDS(path)

    return administrator.AdminPodcast(datastore)


def main():
    parser = argparse.ArgumentParser(description="Manage your One Page Podcast")
    parser.add_argument("path", type=str, help="Path for datastore.")

    subparsers = parser.add_subparsers(title="Commands", required=True)

    make_channel_parser(subparsers.add_parser("initialize"))
    create_episode_parser(subparsers.add_parser("create-episode"))

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
