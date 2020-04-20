#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path
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


def command_parser():
    """Produce the command line parser"""
    parser = argparse.ArgumentParser(
        description="CLI for your One Page Podcast")

    constructor = parser.add_subparsers(title="Subcommands")
    _add_database_command(constructor)
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
