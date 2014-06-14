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

from __future__ import print_function

import sys
import urllib
import urlparse
import xml.etree.ElementTree as etree

import response
import status


class RequestXml(object):
    def __init__(self, xml):
        self.root = etree.fromstring(xml)

    def find(self, *args):
        return self._walk(self.root, args)

    def _walk(self, element, path):
        if element.tag == path[0]:
            path = path[1:]
            if not path:
                return [child.tag for child in element]

            for child in element:
                r = self._walk(child, path)
                if r is not None:
                    return r

        return None


class WebDavRequestHandler(object):
    def __init__(self, backend):
        self.backend = backend

    def handle(self, method, host, path, headers, body):
        func = getattr(self, "do_" + method, None)
        if func:
            try:
                return func(host, path, headers, body)
            except:
                import traceback
                print(traceback.format_exc(), file=sys.stderr)

                return response.Response(status.INTERVAL_SERVER_ERROR)
        else:
            return response.Response(status.NOT_IMPLEMENTED)

    def do_options(self, host, path, headers, body):
        methods = []

        for method in dir(self):
            if method.startswith("do_"):
                methods.append(method[3:].upper())

        return response.Response(status.OK,
                                 {"Allow": ",".join(methods)})

    def do_propfind(self, host, path, headers, body):
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

    def do_head(self, host, path, headers, body):
        return self.backend.head(path)

    def do_get(self, host, path, headers, body):
        return self.backend.get(path)

    def do_put(self, host, path, headers, body):
        content_length = headers.get("Content-Length")
        if content_length is not None:
            if content_length:
                content_length = int(content_length)
            else:
                content_length = 0  # gvfs/1.12.1 sends Content-Length header without value

            return self.backend.put(path, content_length, body)
        else:
            return response.Response(status.LENGTH_REQUIRED)

    def do_mkcol(self, host, path, headers, body):
        return self.backend.mkcol(path)

    def do_delete(self, host, path, headers, body):
        return self.backend.delete(path)

    def do_move(self, host, path, headers, body):
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

    def do_copy(self, host, path, headers, body):
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

    def do_proppatch(self, path, headers, body):
        return response.Response(status.NOT_IMPLEMENTED)
