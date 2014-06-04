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

import urllib
import urlparse

import response
import status
from davxml import RequestXml


class RequestHandler(object):
    Allow = ["OPTIONS",
             "PROPFIND",
             "HEAD",
             "GET",
             "PUT",
             "MKCOL",
             "DELETE",
             "COPY",
             "MOVE",
             "PROPPATCH"]

    def __init__(self, backend):
        self.backend = backend

    def handle(self, method, host, path, headers, body):
        func = getattr(self, "do_" + method, None)
        if func:
            try:
                return func(host, path, headers, body)
            except:
                import traceback
                print traceback.format_exc()

                return response.Response(status.INTERVAL_SERVER_ERROR)
        else:
            return response.Response(status.NOT_IMPLEMENTED)

    def do_OPTIONS(self, host, path, headers, body):
        return response.Response(status.OK,
                                 {"Allow": ",".join(RequestHandler.Allow)})

    def do_PROPFIND(self, host, path, headers, body):
        # RFC says, we should default to "infinity" if Depth header not given
        # but RFC says also that we do not need to support "inifity" for
        # performance or security reasons. So we default to "1".
        depth = int(headers.get("Depth", 1))

        # TODO if content-length 0 and no body => assume allprop

        content_length = int(headers.get("Content-Length", 0))

        request_xml = RequestXml(body.read(content_length))

        try:
            return self.backend.propfind(path, depth, request_xml)
        except IOError:
            return response.Response(status.NOT_FOUND)

    def do_HEAD(self, host, path, headers, body):
        return self.backend.head(path)

    def do_GET(self, host, path, headers, body):
        return self.backend.get(path)

    def do_PUT(self, host, path, headers, body):
        content_length = headers.get("Content-Length")
        if content_length is not None:
            if content_length:
                content_length = int(content_length)
            else:
                content_length = 0  # gvfs/1.12.1 sends Content-Length header without value

            return self.backend.put(path, content_length, body)
        else:
            return response.Response(status.LENGTH_REQUIRED)

    def do_MKCOL(self, host, path, headers, body):
        return self.backend.mkcol(path)

    def do_DELETE(self, host, path, headers, body):
        return self.backend.delete(path)

    def do_MOVE(self, host, path, headers, body):
        overwrite = headers.get("Overwrite", "T")
        if overwrite not in ("T", "F"):
            return response.Response(status.BAD_REQUEST)

        destination = headers.get("Destination")
        if not destination:
            return response.Response(status.BAD_REQUEST)

        url = urlparse.urlparse(destination)

        if url.netloc.lower() != host.lower():
            return response.Response(status.BAD_GATEWAY)

        dest_path = urllib.unquote(url.path).decode("utf-8")

        return self.backend.move(path, dest_path, overwrite == "T")

    def do_COPY(self, host, path, headers, body):
        overwrite = headers.get("Overwrite", "T")
        if overwrite not in ("T", "F"):
            return response.Response(status.BAD_REQUEST)

        destination = headers.get("Destination")
        if not destination:
            return response.Response(status.BAD_REQUEST)

        url = urlparse.urlparse(destination)

        if url.netloc.lower() != host.lower():
            return response.Response(status.BAD_GATEWAY)

        dest_path = urllib.unquote(url.path).decode("utf-8")

        return self.backend.copy(path, dest_path, overwrite == "T")

    def do_PROPPATCH(self, path, headers, body):
        return response.Response(status.NOT_IMPLEMENTED)
