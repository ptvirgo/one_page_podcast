#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import opp.administrator as administrator
import opp.datastore.json_file as jsf

from pathlib import Path

def channel_parser():
    """Produce an argument parser so that a new channel can be initialized."""

    parser = argparse.ArgumentParser(description="Initialize podcast channel.""")

    parser.add_argument("title", type=str, help="Title")
    parser.add_argument("description", type=str, help="Describe the channel")
    parser.add_argument("link", type=str, help="URL")
    parser.add_argument("author", type=str, help="Podcast author")
    parser.add_argument("email", type=str, help="Author email")
    parser.add_argument("--category", type=str, help="What kind of podcast is this?", default="news")
    parser.add_argument("--language", type=str, help="Language code. Default 'en'", default="en")
    parser.add_argument("--explicit", action=argparse.BooleanOptionalAction, help="Explicit? Default False", default=False)
    parser.add_argument("--keyword", type=str, nargs="*", action="extend", help="Keyword descriptions of the podcast content.")

    return parser

def initialize_channel(path, title, description, link, author, email, language, category, explicit, keywords):
    """Initialize a podcast channel."""
    datastore = jsf.AdminDS(path)
    podcast_admin = administrator.AdminPodcast(datastore)
    podcast_admin.initialize_channel(title, link, description, None, author, email, language, category, explicit, keywords)


def main():
    path = Path("/home/ptvirgo/tmp/opp_test.json")

    parser = channel_parser()
    args = parser.parse_args()

    initialize_channel(path, args.title, args.description, args.link, args.author, args.email, args.language, args.category, args.explicit, args.keyword)


if __name__ == "__main__":
    main()
