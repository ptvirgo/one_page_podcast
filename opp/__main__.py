#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from copy import deepcopy
import yaml
import sys

from opp import app, db, SETTINGS

app.app_context().push()


def _add_database_command(constructor):
    """
    Build a parser that can create or delete the database.
    """
    def manage_database(args):
        """
        Execute database management actions specified by the database sub-command
        """

        if args.action.lower() == "create":
            db.create_all()
            return

        if args.action.lower() == "delete":
            db.drop_all()
            return

        raise ValueError("Invalid command %s" % args.action)

    msg = "Manage the database"
    parser = constructor.add_parser("database", help=msg, description=msg)

    parser.add_argument("action",
                        help='Either "create" or "delete" the database.')
    parser.set_defaults(func=manage_database)


def _add_config_command(constructor):
    """
    Build a parser to produce podcast configs.
    """
    def show_config(args):
        cfg = deepcopy(SETTINGS["podcast"])

        for setting in ["title", "subtitle", "description", "link", "author",
                        "email", "language" "keywords", "category"]:
            new = getattr(cfg, setting, None)

            if new is not None:
                cfg[setting] = new

        if args.explicit:
            cfg["explicit"] = "yes"
        else:
            cfg["explicit"] = "no"

        print(yaml.dump(cfg))

    msg = "Print a configuration file."
    parser = constructor.add_parser("config", help=msg, description=msg)

    parser.add_argument("--title", help="Overwrite title")
    parser.add_argument("--subtitle", help="Overwrite subtitle")
    parser.add_argument("--description",
                        help="Overwrite Podcast description, accepts markdown")
    parser.add_argument("--link", help="Overwrite URL for the podcast")
    parser.add_argument("--author", help="Overwrite Podcast author")
    parser.add_argument("--email",
                        help="Overwrite Email address for the podcast author")
    parser.add_argument("--language",
                        help='Overwrite Podcast language code, eg. "en-us"')
    parser.add_argument("--explicit", help="Mark the podcast as explicit",
                        action="store_const", const=True, default=False)
    parser.add_argument("--keywords", help="Overwrite Podcast keywords",
                        nargs="+")
    parser.add_argument("--category", help="Overwrite Podcast category")
    parser.set_defaults(func=show_config)


def command_parser():
    """Produce the command line parser"""
    parser = argparse.ArgumentParser(
        description="CLI for your One Page Podcast")

    constructor = parser.add_subparsers(title="Subcommands")
    _add_database_command(constructor)
    _add_config_command(constructor)
    return parser


def main():
    """
    Delegate program functions.
    """
    parser = command_parser()
    args = parser.parse_args()

    func = getattr(args, "func", None)

    if func is None:
        parser.print_help(sys.stdout)
        return 1

    func(args)


if __name__ == "__main__":
    sys.exit(main())
