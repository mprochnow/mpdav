# coding: utf-8
#
# This file is part of mpdav.
#
# Foobar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with mpdav.  If not, see <http://www.gnu.org/licenses/>.


class Response(object):
    compliance_class = "1"

    def __init__(self, status, headers={}, body=None):
        self.status = status
        self.headers = {"DAV": Response.compliance_class,
                        "Content-Length": "0"}
        self.headers.update(headers)
        self.body = body
