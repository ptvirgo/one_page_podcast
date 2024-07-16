#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import opp.administrator as administrator
import opp.datastore.json_file as jsf
from uuid import uuid4

from datetime import date
from pathlib import Path


def initialize_channel_parser(parser):
    """Prepare an argument parser so that a new channel can be initialized."""

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


def show_channel_parser(parser):
    """Prepare a parser that will display the channel info."""
    parser.set_defaults(func=show_channel)
    return parser


def show_channel(args):
    podcast_admin = admin_interface(args.path)
    channel = podcast_admin.get_channel()

    if channel.get("keywords") is None:
        keywords = "n/a"
    else:
        keywords = ", ".join(channel["keywords"])

    for key in ["Title", "Description", "Link", "Author", "Email", "Category", "Language", "Explicit"]:
        print(f"{key}: {channel[key.lower()]}")

    print(f"Keywords: {keywords}")


def update_channel_parser(parser):
    """Prepare a parser that will update the channel info."""
    parser.set_defaults(func=update_channel)
    parser.add_argument("--title", type=str, help="Title")
    parser.add_argument("--description", type=str, help="Describe the channel.")
    parser.add_argument("--link", type=str, help="URL")
    parser.add_argument("--author", type=str, help="Podcast author")
    parser.add_argument("--email", type=str, help="Author email")

    parser.add_argument("--category", type=str, help="What kind of podcast is this?", default="news")
    parser.add_argument("--language", type=str, help="Language code. Default 'en'", default="en")
    parser.add_argument("--explicit", action=argparse.BooleanOptionalAction, help="Explicit? Default False", default=False)
    parser.add_argument("--keyword", type=str, nargs="*", action="extend", help="Keyword descriptions of the podcast content.")

    return parser


def update_channel(args):
    """Update the channel."""
    podcast_admin = admin_interface(args.path)
    podcast_admin.update_channel(title=args.title, description=args.description, link=args.link, author=args.author, email=args.email, category=args.category, language=args.language, explicit=args.explicit, keywords=args.keyword)


def create_episode_parser(parser):
    """Prepare a parser that can create a new episode."""
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

    with open(args.file, "rb") as file:
        podcast_admin.create_episode(file, title, description, details["duration"], publication_date, details["audio_format"])


def list_episode_parser(parser):
    """Prepare parser to list episodes."""
    parser.set_defaults(func=list_episodes)

    return parser


def list_episodes(args):
    """List episodes."""
    podcast_admin = admin_interface(args.path)

    for ep in podcast_admin.get_episodes():
        print(f"{ep['guid']}: ({ep['publication_date']}) {ep['title']} - {ep['description']}")


def update_episode_parser(parser):
    """Prepare a parser to update an episode."""
    parser.set_defaults(func=update_episode)
    parser.add_argument("guid", type=str, help="Episode GUID")
    parser.add_argument("--title", type=str, help="Title")
    parser.add_argument("--description", type=str, help="Describe the episode.")
    parser.add_argument("--publication-date", type=str, help="Date in YYYY-MM-DD format.")

    return parser


def update_episode(args):
    """Update an episode."""
    podcast_admin = admin_interface(args.path)

    podcast_admin.update_episode(args.guid, title=args.title, description=args.description, publication_date=args.publication_date)


def delete_episode_parser(parser):
    """Prepare a parser that can delete an episode."""
    parser.set_defaults(func=delete_episode)
    parser.add_argument("guid", type=str, help="Episode GUID")

    return parser


def delete_episode(args):
    """Delete an episode."""
    podcast_admin = admin_interface(args.path)
    podcast_admin.delete_episode(args.guid)


def admin_interface(path_name):
    path = Path(path_name)
    datastore = jsf.AdminDS(path)

    return administrator.AdminPodcast(datastore)


def main():
    parser = argparse.ArgumentParser(description="Manage your One Page Podcast")
    parser.add_argument("path", type=str, help="Path for datastore.")

    subparsers = parser.add_subparsers(title="Commands", required=True)

    initialize_channel_parser(subparsers.add_parser("initialize"))
    show_channel_parser(subparsers.add_parser("show-channel"))
    update_channel_parser(subparsers.add_parser("update-channel"))

    create_episode_parser(subparsers.add_parser("create-episode"))
    list_episode_parser(subparsers.add_parser("list-episodes"))
    update_episode_parser(subparsers.add_parser("update-episode"))
    delete_episode_parser(subparsers.add_parser("delete-episode"))

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
