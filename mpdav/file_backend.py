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

import md5
import mimetypes
import os.path
import shutil
import time

import multi_status
import response
import status

BLOCK_SIZE = 8192  # just an assumption


def epoch2iso8601(ts):
    t = time.localtime(ts)
    tz = (time.altzone if t.tm_isdst else time.timezone) / 3600 * -1

    return time.strftime("%Y-%m-%dT%H:%M:%S", t) + "%+.02d:00" % tz


def epoch2iso1123(ts):
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(ts))


class FileIterator(object):
    def __init__(self, filename):
        self.filename = filename

    def __iter__(self):
        remaining = os.stat(self.filename).st_size
        f = open(self.filename, "rb")

        while remaining > 0:
            r = min(remaining, BLOCK_SIZE)

            yield f.read(r)

            remaining -= r

        f.close()


class FileBackend(object):
    def __init__(self, root, show_hidden=False, base_path="/"):
        self.root = os.path.abspath(root)
        self.show_hidden = show_hidden
        self.base_path = base_path.rstrip("/")

    def propfind(self, path, depth, request_xml):
        # TODO implement support for allprop

        paths = self._build_paths(path, depth)

        return multi_status.MultiStatus(self._get_properties(paths, request_xml))

    def _build_paths(self, path, depth):
        path = path.strip("/")
        path = os.path.abspath(os.path.join(self.root, path))

        if path.startswith(self.root) and os.path.exists(path):
            paths = [path]

            if os.path.isdir(path) and depth == 1:
                for p in os.listdir(path):
                    if self._show(p):
                        paths.append(os.path.join(path, p))

            for i, p in enumerate(paths):
                if os.path.isdir(p) and p[:-1] != "/":
                    paths[i] = p + "/"

            return paths

        raise IOError

    def _show(self, filename):
        return self.show_hidden or not filename.startswith(".")

    def _get_properties(self, paths, request_xml):
        result = []

        for p in paths:
            prop_stat = multi_status.PropStat(status.OK)

            try:
                st = os.stat(p)
                fs_st = os.statvfs(p.encode("utf-8"))
            except:
                continue

            name = self._build_displayname(p)
            is_dir = os.path.isdir(p)

            for property_ in request_xml.find("{DAV:}propfind", "{DAV:}prop"):
                if property_ == "{DAV:}resourcetype":
                    prop_stat.add_resourcetype(is_dir)

                elif property_ == "{DAV:}creationdate":
                    prop_stat.add_creationdate(epoch2iso8601(st.st_ctime))

                elif property_ == "{DAV:}displayname":
                    prop_stat.add_displayname(name)

                elif property_ == "{DAV:}getcontentlength":
                    if not is_dir:
                        prop_stat.add_getcontentlength(st.st_size)

                elif property_ == "{DAV:}getcontenttype":
                    if not is_dir:
                        ct = mimetypes.guess_type(p)[0] or "application/octet-stream"
                        prop_stat.add_getcontenttype(ct)

                elif property_ == "{DAV:}getetag":
                    prop_stat.add_getetag(md5.new("%s%s" % (name.encode("utf-8"), st.st_mtime)).hexdigest())

                elif property_ == "{DAV:}getlastmodified":
                    prop_stat.add_getlastmodified(epoch2iso1123(st.st_mtime))

                elif property_ == "{DAV:}quota-available-bytes":
                    prop_stat.add_quota_available_bytes(fs_st.f_bavail * fs_st.f_frsize)

                elif property_ == "{DAV:}quota-used-bytes":
                    prop_stat.add_quota_used_bytes((fs_st.f_blocks - fs_st.f_bavail) * fs_st.f_frsize)

                else:
                    print "Request for not supported property %s" % property_

            href = self.base_path + p[len(self.root):]

            result.append(multi_status.Response(href, prop_stat))

        return result

    def _build_displayname(self, path):
        cut = len(self.root)
        return os.path.basename(os.path.normpath(path[cut:]))

    def head(self, path):
        return self.get(path, False)

    def get(self, path, with_body=True):
        filename = os.path.abspath(os.path.join(self.root, path.strip("/")))

        if not filename.startswith(self.root):
            return response.Response(status.FORBIDDEN)
        elif not os.path.exists(filename):
            return response.Response(status.NOT_FOUND)

        if os.path.isdir(filename):
            body = None
            content_length = "0"

            if with_body:
                body = self._get_collection(filename)
                content_length = str(len(body))

            return response.Response(status.OK,
                                     {"Content-Type": "text/html",
                                      "Content-Length": content_length},
                                     [body] if with_body else None)
        else:
            st = os.stat(filename)

            headers = {"Content-Type": mimetypes.guess_type("filename")[0] or "application/octet-stream",
                       "Content-Length": str(st.st_size)}

            return response.Response(status.OK,
                                     headers,
                                     FileIterator(filename) if with_body else None)

    def _get_collection(self, path):
        filenames = os.listdir(path)

        directories = [f for f in filenames if self._show(f) and os.path.isdir(os.path.join(path, f))]
        files = [f for f in filenames if self._show(f) and os.path.isfile(os.path.join(path, f))]

        directories.sort(key=lambda d: d.lower())
        files.sort(key=lambda f: f.lower())

        filenames = directories + files

        result = u"""\
<html>
<head>
<title>Content of %s</title>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
</head>
<body>
<ul style="padding:0;margin:0;list-style-type:none;">
""" % os.path.basename(path)

        tplDirectory = """<li><a href="%s">[%s]</a></li>\n"""
        tplFile = """<li><a href="%s">%s</a></li>\n"""

        for f in filenames:
            p = os.path.join(path, f)
            href = p[len(self.root):]

            if os.path.isdir(p):
                result += tplDirectory % (href, f)
            else:
                result += tplFile % (href, f)

        result += """\
</ul>
</body>
</html>
"""

        return result.encode("utf-8")

    def put(self, path, content_length, body):
        filename = os.path.abspath(os.path.join(self.root, path.strip("/")))

        if not filename.startswith(self.root):
            return response.Response(status.FORBIDDEN)
        elif os.path.isdir(filename):
            return response.Response(status.NOT_ALLOWED)
        elif not os.path.isdir(os.path.dirname(filename)):
            return response.Response(status.CONFLICT)

        created = not os.path.exists(filename)

        f = open(filename, "wb")
        if content_length:
            remaining = content_length
            while remaining > 0:
                buf = body.read(min(remaining, BLOCK_SIZE))

                if len(buf):
                    f.write(buf)
                    remaining -= len(buf)
                else:
                    break

        f.close()

        if created:
            return response.Response(status.CREATED)
        else:
            return response.Response(status.NO_CONTENT)

    def mkcol(self, path):
        dirname = os.path.abspath(os.path.join(self.root, path.strip("/")))

        if not dirname.startswith(self.root):
            return response.Response(status.FORBIDDEN)
        elif os.path.exists(dirname):
            return response.Response(status.NOT_ALLOWED)
        elif not os.path.isdir(os.path.dirname(dirname)):
            return response.Response(status.CONFLICT)

        os.mkdir(dirname)

        return response.Response(status.CREATED, {}, None)

    def delete(self, path):
        filename = os.path.abspath(os.path.join(self.root, path.strip("/")))

        if not filename.startswith(self.root):
            return response.Response(status.FORBIDDEN)

        if os.path.isfile(filename):
            os.remove(filename)
        elif os.path.isdir(filename):
            shutil.rmtree(filename)
        elif not os.path.exists(filename):
            return response.Response(status.NOT_FOUND)

        return response.Response(status.NO_CONTENT)

    def move(self, src, dst, overwrite):
        if not dst.startswith(self.base_path):
            return response.Response(status.FORBIDDEN)

        source = os.path.join(self.root, src.strip("/"))
        source = os.path.abspath(source)

        destination = dst[len(self.base_path):]
        destination = os.path.join(self.root, destination.strip("/"))
        destination = os.path.abspath(destination)

        if not source.startswith(self.root) or not destination.startswith(self.root):
            return response.Response(status.FORBIDDEN)
        elif source == destination:
            return response.Response(status.FORBIDDEN)
        elif not os.path.isdir(os.path.dirname(destination)):
            return response.Response(status.CONFLICT)
        elif not overwrite and os.path.exists(destination):
            return response.Response(status.PRECONDITION_FAILED)

        created = not os.path.exists(destination)

        if os.path.isdir(destination):
            shutil.rmtree(destination)
        elif os.path.isfile(destination):
            os.remove(destination)

        if os.path.isdir(source):
            shutil.move(source, destination)
        elif os.path.isfile(source):
            os.rename(source, destination)  # TODO will this work between partitions?

        if created:
            return response.Response(status.CREATED)
        else:
            return response.Response(status.NO_CONTENT)

    def copy(self, src, dst, overwrite):
        if not dst.startswith(self.base_path):
            return response.Response(status.BAD_REQUEST)

        source = os.path.join(self.root, src.strip("/"))
        source = os.path.abspath(source)

        destination = dst[len(self.base_path):]
        destination = os.path.join(self.root, destination.strip("/"))
        destination = os.path.abspath(destination)

        if not source.startswith(self.root) or not destination.startswith(self.root):
            return response.Response(status.FORBIDDEN)
        elif source == destination:
            return response.Response(status.FORBIDDEN)
        elif not os.path.isdir(os.path.dirname(destination)):
            return response.Response(status.CONFLICT)
        elif not overwrite and os.path.exists(destination):
            return response.Response(status.PRECONDITION_FAILED)

        created = not os.path.exists(destination)

        if os.path.isdir(destination):
            shutil.rmtree(destination)
        elif os.path.isfile(destination):
            os.remove(destination)

        if os.path.isdir(source):
            shutil.copytree(source, destination)
        elif os.path.isfile(source):
            shutil.copyfile(source, destination)

        if created:
            return response.Response(status.CREATED)
        else:
            return response.Response(status.NO_CONTENT)
