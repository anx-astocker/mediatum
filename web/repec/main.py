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
import logging

from core import users
from core.transition import httpstatus

from web.repec.content import CollectionArchiveContent, CollectionSeriesContent


logg = logging.getLogger("repec")


def collection(req):
    logg.debug("RePEc Collection")
    return collection_arch(req)


def collection_arch(req):
    logg.debug("RePEc Collection Archive")

    req['Content-Type'] = 'text/plain'

    content = CollectionArchiveContent(req)
    return content.respond()


def collection_seri(req):
    logg.debug("RePEc Collection Series")

    req['Content-Type'] = 'text/plain'

    content = CollectionSeriesContent(req)
    return content.respond()


def journl(req):
    logg.debug("RePEc Journal")
    pass


def journl_rdf(req):
    logg.debug("RePEc Journal RDF")
    pass


def wpaper(req):
    logg.debug("RePEc Paper")
    pass


def wpaper_rdf(req):
    logg.debug("RePEc Paper RDF")
    pass