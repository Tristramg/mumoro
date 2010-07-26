# -*- coding: utf-8 -*-

import hashlib
import string
import datetime

from sqlalchemy import *

class shortURL:
    def __init__(self,metadata):
        self.metadata = metadata
        self.hash_table = Table('hurl', self.metadata,useexisting=True)

    def addRouteToDatabase(self,lonMap,latMap,zoom,lonStart,latStart,lonDest,latDest,addressStart,addressDest):
        h = hashlib.md5()
	chrone = datetime.datetime.now()
        h.update(addressStart.encode("utf-8"))
        h.update(addressDest.encode("utf-8"))
        h.update(str(lonStart))
        h.update(str(latStart))
        h.update(str(lonDest))
        h.update(str(latDest))
        h.update(str(lonMap))
        h.update(str(latMap))
        h.update(str(zoom))
	h.update(str(chrone).encode("utf-8"))
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
                   'chrone': chrone}
        )
        return h.hexdigest()[0:16]

    def getDataFromHash(self,value):
        s = self.hash_table.select(self.hash_table.c.id == value)
        rs = s.execute()
        res = []
        for u in rs:
            res.append( u.id )
            res.append( u.zoom )
            res.append( u.lonMap )
            res.append( u.latMap )
            res.append( u.lonStart )
            res.append( u.latStart )
            res.append( u.lonDest )
            res.append( u.latDest )
            res.append( u.addressStart.encode("utf-8") )
            res.append( u.addressDest.encode("utf-8") )
            return res
        return res 

#if __name__ == "__main__":
#    engine = create_engine('sqlite:////home/ody/takis.db')
#    metadata = MetaData(bind = engine)
#    v = shortURL(metadata)
#    print v.getDataFromHash('5c03d48b900b614d')
#    v.addRouteToDatabase(1.46,48.3,15,6.22,65.33,43.21,43.11,'Takis the cat','Toulouse clemence')


