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

import xml.etree.ElementTree as etree
import response
import status

etree.register_namespace("D", "DAV:")


def indent_xml(element):
    def indent(e, lvl=0):
        i = "\n" + lvl * "  "
        if len(e):
            if not e.text or not e.text.strip():
                e.text = i + "  "
            if not e.tail or not e.tail.strip():
                e.tail = i
            for e in e:
                indent(e, lvl + 1)
            if not e.tail or not e.tail.strip():
                e.tail = i
        else:
            if lvl and (not e.tail or not e.tail.strip()):
                e.tail = i

    indent(element)

    class dummy():
        pass

    data = []

    f = dummy()
    f.write = data.append

    etree.ElementTree(element).write(f, encoding="UTF-8")

    return "".join(data)


class PropStat(object):
    def __init__(self, status):
        self.xml = etree.Element("{DAV:}propstat")
        self.prop = etree.SubElement(self.xml, "{DAV:}prop")
        etree.SubElement(self.xml, "{DAV:}status").text = "HTTP/1.1 %s %s" % status

    def add_creationdate(self, creationdate):
        etree.SubElement(self.prop, "{DAV:}creationdate").text = creationdate

    def add_displayname(self, displayname):
        etree.SubElement(self.prop, "{DAV:}displayname").text = displayname

    def add_getcontentlength(self, content_length):
        etree.SubElement(self.prop, "{DAV:}getcontentlength").text = "%s" % content_length

    def add_getcontenttype(self, content_type):
        etree.SubElement(self.prop, "{DAV:}getcontenttype").text = content_type

    def add_getetag(self, etag):
        etree.SubElement(self.prop, "{DAV:}getetag").text = etag

    def add_getlastmodified(self, last_modified):
        etree.SubElement(self.prop, "{DAV:}getlastmodified").text = last_modified

    def add_resourcetype(self, collection):
        resourcetype = etree.SubElement(self.prop, "{DAV:}resourcetype")
        if collection:
            etree.SubElement(resourcetype, "{DAV:}collection")

    def add_quota_available_bytes(self, byte_count):
        etree.SubElement(self.prop, "{DAV:}quota-available-byte_count").text = "%s" % byte_count

    def add_quota_used_bytes(self, byte_count):
        etree.SubElement(self.prop, "{DAV:}quota-used-byte_count").text = "%s" % byte_count


class Response(object):
    def __init__(self, href, child=None):
        self.xml = etree.Element("{DAV:}response")
        etree.SubElement(self.xml, "{DAV:}href").text = href
        if child is not None:
            self.add(child)

    def add(self, child):
        self.xml.append(child.xml)


class MultiStatus(response.Response):
    def __init__(self, childs=None):
        response.Response.__init__(self, status.MULTI_STATUS)

        self.multistatus = etree.Element("{DAV:}multistatus")
        for c in childs:
            self.multistatus.append(c.xml)

        xml = etree.tostring(self.multistatus, encoding="UTF-8")

        self.headers["Content-Length"] = str(len(xml))
        self.body = [xml]
