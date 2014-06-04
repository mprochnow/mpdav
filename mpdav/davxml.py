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


class RequestXml(object):
    def __init__(self, xml):
        self.root = etree.fromstring(xml)

    def find(self, *args):
        return self._walk(self.root, args)

    def _walk(self, element, path):
        if element.tag == "{DAV:}" + path[0]:
            path = path[1:]
            if not path:
                return [child.tag[6:] for child in element]

            for child in element:
                r = self._walk(child, path)
                if r is not None:
                    return r

        return None


def test_xml_parser():
    propfind = """\
<?xml version="1.0" encoding="utf-8" ?>
<D:propfind xmlns:D="DAV:">
  <D:prop xmlns:R="http://ns.example.com/boxschema/">
    <D:bigbox/>
    <D:author/>
    <D:DingALing/>
    <D:Random/>
  </D:prop>
</D:propfind>"""

    p = RequestXml(propfind)
    print p.find("propfind")
    print p.find("propfind", "prop")
    print p.find("propfind", "prop", "bigbox")
    print p.find("propfind", "prop", "author")
    print p.find("propfind", "prop", "author", "foobar")

    for e in p.find("propfind", "prop"):
        print type(e), e


if __name__ == "__main__":
    test_xml_parser()
