#!/usr/bin/env python
# coding: utf-8
#
# This file is part of mpdav.
#
# mpdav is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# mpdav is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with mpdav.  If not, see <http://www.gnu.org/licenses/>.

from wsgiref.simple_server import make_server
import mpdav


class DavWsgiApp(object):
    def __init__(self):
        self.dav = mpdav.RequestHandler(mpdav.FileBackend("."))

    def __call__(self, environ, start_response):
        method = environ["REQUEST_METHOD"].lower()
        host = environ["HTTP_HOST"]
        path = environ["PATH_INFO"].decode("utf-8")
        headers = self._build_headers(environ)
        body = environ["wsgi.input"]

        response = self.dav.handle(method, host, path, headers, body)

        start_response("%d %s" % (response.status),
                       [(k, v) for k, v in response.headers.iteritems()])

        if response.body:
            return response.body
        else:
            return []

    def _build_headers(self, environ):
        result = mpdav.HeadersDict()

        for k, v in environ.iteritems():
            if k.startswith("HTTP_"):
                result[k[5:].replace("_", "-")] = v
            elif k.startswith("CONTENT_"):
                result[k.replace("_", "-")] = v

        return result


if __name__ == "__main__":
    s = make_server('', 8000, DavWsgiApp())
    s.serve_forever()
