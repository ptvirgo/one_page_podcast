#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from cleantext import clean
from datetime import datetime
import mutagen
import os
import shutil

from opp import app, db, DEFAULT_CFG, SETTINGS, AudioFormat, AudioFile, \
    Episode, Keyword, format_datetime, format_episode_keywords

app.app_context().push()


def manage_database(args):
    """
    Execute database management actions specified by the database sub-command
    """
    if args.create:
        db.create_all()

    if args.delete:
        db.drop_all()


def add_database_command(constructor):
    """
    Build a parser that can create or delete the database.
    """
    msg = "Manage the database"
    parser = constructor.add_parser("database", help=msg, description=msg)

    parser.add_argument("--create", default=False, action="store_const",
                        const=True, help="Create a fresh database")
    parser.add_argument("--delete", default=False, action="store_const",
                        const=True, help="Delete an existing database")
    parser.set_defaults(func=manage_database)
    return parser


def produce_configs(args):
    """
    Produce configuration information as requested by the config sub-command
    """
    if args.base:
        with open(DEFAULT_CFG, "r") as f:
            print(f.read())


def add_config_command(constructor):
    """
    Build a parser that can print configuration data
    """
    msg = "Print configuration info"
    parser = constructor.add_parser("config", help=msg, description=msg)
    parser.add_argument("--base", default=False, action="store_const",
                        const=True, help="Print a base configuration template")
    parser.set_defaults(func=produce_configs)
    return parser


def list_episodes(args):
    """
    Execute episode management commands as requested by the episode sub-command
    """
    episodes = Episode.query.order_by(Episode.published.desc()).all()

    for episode in episodes:
        print("%d: %s (%s) - %s [%s]" % (
            episode.item_id,
            format_datetime(episode.published),
            episode.audio_file.file_name,
            episode.title, format_episode_keywords(episode.keywords)))


def add_list_command(constructor):
    """
    Build a parser to list episodes
    """
    msg = "List all episodes"
    parser = constructor.add_parser("list", help=msg, description=msg)
    parser.set_defaults(func=list_episodes)
    return parser


def create_episode(args):
    """
    Create an episode as requested by the episode sub-command
    """
    if args.date is None:
        published = datetime.utcnow()
    else:
        year, month, day = args.date.split("-")
        published = datetime(int(year), int(month), int(day))

    episode = Episode(
        title=args.title,
        published=published,
        description=args.description,
        explicit=args.explicit)

    if args.keywords is not None:
        for word in args.keywords:
            word = clean(word)
            kw = Keyword.query.filter_by(word=word).first()

            if kw is None:
                kw = Keyword(word=word)

            episode.keywords.append(kw)

    with open(args.file, "rb") as f:
        new_name = clean(os.path.basename(args.file))
        new_path = os.path.join(
            SETTINGS["configuration"]["directories"]["media"], new_name)

        af = mutagen.File(f)

    audio_file = AudioFile(
        file_name=new_name,
        audio_format=AudioFormat[af.__class__.__name__],
        length=os.path.getsize(args.file),
        duration=round(af.info.length))

    episode.audio_file = audio_file
    db.session.add(episode)
    db.session.commit()

    shutil.copy(args.file, new_path)


def add_create_command(constructor):
    """
    Build a parser to add new episodes
    """
    msg = "Create a new episode"
    parser = constructor.add_parser("create", help=msg, description=msg)
    parser.add_argument("file", help="Audio file containing the episode")
    parser.add_argument("title", help="Episode title")
    parser.add_argument("description", help="Describe the episode")

    parser.add_argument("--explicit", default=False, action="store_const",
                        const=True, help="Mark as explicit")
    parser.add_argument(
        "--keywords", help="As many keywords as you need", nargs="*")
    parser.add_argument(
        "--date", help="Alternate date, must be YYYY-MM-DD")
    parser.set_defaults(func=create_episode)
    return parser


def delete_episode(args):
    """
    Delete an episode, per arguements
    """
    episode = Episode.query.filter_by(item_id=args.episode_id).one()
    file_name = os.path.join(
            SETTINGS["configuration"]["directories"]["media"],
            episode.audio_file.file_name)

    db.session.delete(episode)
    db.session.commit()

    if args.rm:
        os.remove(file_name)


def add_delete_command(constructor):
    """
    Build a parser to delete episodes
    """
    msg = "Delete an episode"
    parser = constructor.add_parser("delete", help=msg, description=msg)
    parser.add_argument("episode_id", type=int,
                        help="ID Number of the episode")
    parser.add_argument("--rm", default=False, action="store_const",
                        const=True, help="Remove the episode audio file")

    parser.set_defaults(func=delete_episode)
    return parser


def add_episode_command(constructor):
    """
    Build a parser that can manage episodes
    """
    msg = "Manage episodes"
    parser = constructor.add_parser("episode", help=msg, description=msg)
    episode_constructor = parser.add_subparsers(
        title="Episode management commands")
    add_list_command(episode_constructor)
    add_create_command(episode_constructor)
    add_delete_command(episode_constructor)
    return parser


def command_parser():
    """
    Organize contsruction of the primary argument parser and sub-commands
    """
    parser = argparse.ArgumentParser(
        description="CLI for your One Page Podcast")
    constructor = parser.add_subparsers(title="SubCommands")
    add_database_command(constructor)
    add_config_command(constructor)
    add_episode_command(constructor)

    return parser


def main():
    """
    Delegate program functions.
    """
    parser = command_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
