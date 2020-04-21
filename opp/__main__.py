#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys

from opp import app, db

app.app_context().push()


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


def command_parser():
    """Produce the command line parser"""
    parser = argparse.ArgumentParser(
        description="Set up your podcast database")

    parser.add_argument("action",
                        help='Either "create" or "delete" the database.')
    return parser


def main():
    """
    Delegate program functions.
    """
    parser = command_parser()
    args = parser.parse_args()
    manage_database(args)


if __name__ == "__main__":
    sys.exit(main())
