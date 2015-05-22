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
from web.repec.content import *


def collection(req):
    req['Content-Type'] = 'text/html; charset=utf-8'

    content = HTMLCollectionContent(req)
    return content.respond()


def collection_arch(req):
    req['Content-Type'] = 'text/plain; charset=utf-8'

    content = CollectionArchiveContent(req)
    return content.respond()


def collection_seri(req):
    req['Content-Type'] = 'text/plain; charset=utf-8'

    content = CollectionSeriesContent(req)
    return content.respond()


def journl(req):
    req['Content-Type'] = 'text/html; charset=utf-8'

    content = HTMLCollectionJournalContent(req)
    return content.respond()


def journl_rdf(req):
    req['Content-Type'] = 'text/plain; charset=utf-8'

    content = CollectionJournalContent(req)
    return content.respond()


def wpaper(req):
    req['Content-Type'] = 'text/html; charset=utf-8'

    content = HTMLCollectionPaperContent(req)
    return content.respond()


def wpaper_rdf(req):
    req['Content-Type'] = 'text/plain; charset=utf-8'

    content = CollectionPaperContent(req)
    return content.respond()



def ecbook(req):
    req['Content-Type'] = 'text/html; charset=utf-8'

    content = HTMLCollectionBookContent(req)
    return content.respond()


def ecbook_rdf(req):
    req['Content-Type'] = 'text/plain; charset=utf-8'

    content = CollectionBookContent(req)
    return content.respond()
