"""
 mediatum - a multimedia content repository

 Copyright (C) 2007 Arne Seifert <seiferta@in.tum.de>
 Copyright (C) 2007 Matthias Kramm <kramm@in.tum.de>
 Copyright (C) 2015 Andreas Stocker <as@anexia.at>

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import json
import logging

import core.acl
import core.config as config
import core.users as users
import core.xmlnode as xmlnode
import core.tree as tree
from utils.utils import *
from core.acl import AccessData
from core.metatype import Context
from core.translation import lang
from core.tree import db
from web.frontend.frame import getNavigationFrame
from web.frontend.content import getContentArea, ContentNode
from schema.schema import getMetadataType, getMetaType
from core.transition import httpstatus


logg = logging.getLogger("repec")


def collection(req):
    print "RePEc Collection"
    pass


def collection_arch(req):
    print "RePEc Collection Archive"
    pass


def collection_seri(req):
    print "RePEc Collection Serialized"
    pass


def journl(req):
    print "RePEc Journal"
    pass


def journl_rdf(req):
    print "RePEc Journal RDF"
    pass


def wpaper(req):
    print "RePEc Paper"
    pass


def wpaper_rdf(req):
    print "RePEc Paper RDF"
    pass