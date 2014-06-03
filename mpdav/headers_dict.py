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

import collections


class HeadersDict(collections.MutableMapping):
    def __init__(self):
        self.store = dict()

    def __getitem__(self, key):
        return self.store[key.lower()]

    def __setitem__(self, key, value):
        self.store[key.lower()] = value

    def __delitem__(self, key):
        del self.store[key.lower()]

    def __contains__(self, key):
        return key.lower() in self.store

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)
