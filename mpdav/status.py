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

OK = (200, "OK")
CREATED = (201, "Created")
NO_CONTENT = (204, "No Content")
MULTI_STATUS = (207, "Multi-Status")

BAD_REQUEST = (400, "Bad Request")
FORBIDDEN = (403, "Forbidden")
NOT_FOUND = (404, "Not Found")
NOT_ALLOWED = (405, "Method Not Allowed")
CONFLICT = (409, "Conflict")
LENGTH_REQUIRED = (411, "Length Required")
PRECONDITION_FAILED = (412, "Precondition Failed")
LOCKED = (423, "Locked")
FAILED_DEPENDENCY = (424, "Failed Dependency")

INTERVAL_SERVER_ERROR = (500, "Internal Server Error")
NOT_IMPLEMENTED = (501, "Not Implemented")
BAD_GATEWAY = (502, "Bad Gateway")
INSUFFICIENT_STORAGE = (507, "Insufficient Storage")
