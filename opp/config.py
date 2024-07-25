#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import environ
from pathlib import Path

import opp.administrator as administrator
import opp.datastore.json_file as jsf
import opp.visitor as visitor


def datastore_dir():

    if "OPP" in environ:
        return Path(environ["OPP"])

    return Path(environ["HOME"]) / ".config/opp/"


def init_visitor():
    global VISIT_PODCAST
    visitor_ds = jsf.VisitorDS(datastore_dir())
    VISIT_PODCAST = visitor.VisitPodcast(visitor_ds)


def init_admin():
    global ADMIN_PODCAST

    admin_ds = jsf.AdminDS(datastore_dir())
    ADMIN_PODCAST = administrator.AdminPodcast(admin_ds)
