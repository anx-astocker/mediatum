"""
 mediatum - a multimedia content repository

 Copyright (C) 2007 Arne Seifert <seiferta@in.tum.de>
 Copyright (C) 2007 Matthias Kramm <kramm@in.tum.de>
 Copyright (C) 2011 Werner Neudenberger <neudenberger@ub.tum.de>


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

import sys
import re
import time
import locale

import logging
import BaseHTTPServer
response_code_dict = BaseHTTPServer.BaseHTTPRequestHandler.responses

LOCALES = ["en_US.UTF-8", "english", "german"]

#import core.tree as tree
#collections_id = tree.getRoot('collections').id

try:
    locale.setlocale(locale.LC_ALL, LOCALES[0])  # for thousands separator
except:
    pass

try:
    locale.setlocale(locale.LC_ALL, LOCALES[1])  # for thousands separator
except:
    pass

from . import handlers

SERVICES_URL_HAS_HANDLER = 1
SERVICES_URL_SIMPLE_REWRITE = 2

urls = [
    ["GET", "/index.html$", handlers.serve_file, ("/static/index.html", {}, {'filepath': 'index.html'}), SERVICES_URL_SIMPLE_REWRITE, None],
    ["GET", "/$", handlers.serve_file,
            ("/static/index.html", {}, {'filepath': 'index.html'}), SERVICES_URL_SIMPLE_REWRITE, None],

    ["GET", "/scheme/(?P<name>.*)/{0,1}$", handlers.get_sheme, None, SERVICES_URL_HAS_HANDLER, None],
    ["GET", "/appdefinitions/(?P<name>.*)/{0,1}$", handlers.get_app_definitions, None, SERVICES_URL_HAS_HANDLER, None],

    ["GET", "/static/(?P<filepath>.*)$", handlers.serve_file, None, SERVICES_URL_HAS_HANDLER, None],
]

DEBUG = True


def request_handler(req):

    handle_starttime = time.time()
    matched = False
    req_path = req.path
    for method, pattern, handler_func, rewrite_target, url_flags, data in urls:
        if method and method == req.command:
            m = re.match(pattern, req_path)
            if m:

                matched = True

                if url_flags == SERVICES_URL_HAS_HANDLER:
                    handle_path = req.path
                    handle_params = req.params
                    response_code, bytes_sent, d = handler_func(req, handle_path, handle_params, data, **m.groupdict())
                    break

                if url_flags == SERVICES_URL_SIMPLE_REWRITE:
                    handle_path = rewrite_target[0]

                    handle_params = req.params.copy()
                    for key, value in rewrite_target[1].items():
                        handle_params[key] = value

                    argsdict = m.groupdict().copy()
                    for key, value in rewrite_target[2].items():
                        argsdict[key] = value

                    response_code, bytes_sent, d = handler_func(req, handle_path, handle_params, data, **argsdict)
                    break

    # try to call default handler, if no match
    if not matched:
        try:
            if getattr(handlers, 'default_handler'):
                response_code, bytes_sent = handlers.default_handler(req)
        except:
            response_code, bytes_sent = '404', 0

    handle_endtime = time.time()
    handle_duration = "%.3f sec." % (handle_endtime - handle_starttime)

    response_code_description = response_code_dict[int(response_code)][0]

    useragent = 'unknown'
    try:
        cutoff = 60
        useragent = req.request_headers['user-agent']
        if len(useragent) > cutoff:
            useragent = useragent[0:cutoff] + '...'
    except:
        pass

    s = "services %s '%s' (%s): %s for %s bytes for service request (%s, %s, %s) - (user-agent: %s)" % (req.ip,
                                                                                                        str(response_code),
                                                                                                        response_code_description,
                                                                                                        handle_duration,
                                                                                                        locale.format(
                                                                                                            "%d",
                                                                                                            bytes_sent,
                                                                                                            1),
                                                                                                        req.command,
                                                                                                        req.fullpath,
                                                                                                        req.params,
                                                                                                        useragent)

    if DEBUG and matched and 'timetable' in d:
        timesum = 0
        s += '\n' + ('-' * 80)
        s += "\n| timetable for request (%s, %s, %s)" % (req.command, req.fullpath, handle_params)
        for i, [step, executiontime] in enumerate(d['timetable']):
            s += "\n|  %2d. step: %.3f sec.: %s" % (i, executiontime, step)
            timesum += executiontime
        s += "\n| sum of execution times: %.3f sec.: %s bytes returned" % (timesum, locale.format("%d", bytes_sent, 1))
        s += '\n' + ('-' * 80)

    logging.getLogger('services').info(s)
    sys.stdout.flush()

    if not matched:
        return req.error(404, "File " + req.path + " not found")

    return response_code
