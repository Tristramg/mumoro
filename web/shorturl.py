# -*- coding: utf-8 -*-

#    This file is part of Mumoro.
#
#    Mumoro is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Mumoro is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Mumoro.  If not, see <http://www.gnu.org/licenses/>.
#
#    © Université de Toulouse 1 2010
#    Author: Tristram Gräbener, Odysseas Gabrielides

import hashlib
import string
import datetime

from sqlalchemy import *

class shortURL:
    def __init__(self,metadata):
        self.metadata = metadata
        self.hash_table = Table('hurl', self.metadata,useexisting=True)

    def addRouteToDatabase(self,lonMap,latMap,zoom,lonStart,latStart,lonDest,latDest,addressStart,addressDest, time):
        h = hashlib.md5()
        h.update(addressStart.encode("utf-8"))
        h.update(addressDest.encode("utf-8"))
        h.update(str(lonStart))
        h.update(str(latStart))
        h.update(str(lonDest))
        h.update(str(latDest))
        h.update(str(lonMap))
        h.update(str(latMap))
        h.update(str(zoom))
        h.update(str(time))
        i = self.hash_table.insert()
        i.execute({'id': h.hexdigest()[0:16],
                   'zoom': zoom,
                   'lonMap': lonMap,
                   'latMap': latMap,
                   'lonStart': lonStart,
                   'latStart': latStart,
                   'lonDest': lonDest,
                   'latDest': latDest,
                   'addressStart': addressStart,
                   'addressDest': addressDest,
                   'chrone': datetime.datetime.strptime(time, "%d/%m/%Y %H:%M")}
        )
        return h.hexdigest()[0:16]

    def getDataFromHash(self,value):
        s = self.hash_table.select(self.hash_table.c.id == value)
        u = s.execute().first()
        return [u.id, u.zoom, u.lonMap, u.latMap,
                u.lonStart, u.latStart, u.lonDest, u.latDest,
                u.addressStart.encode("utf-8"), u.addressDest.encode("utf-8"),
                u.chrone]

