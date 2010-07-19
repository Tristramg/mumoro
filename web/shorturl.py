# -*- coding: utf-8 -*-

import hashlib
import string
import config
import datetime

from sqlalchemy import *
from sqlalchemy.orm import *

class shortURL:
    def __init__(self,metadata, session):
        self.metadata = metadata
        self.session = session
        self.hash_table = Table('hurl', self.metadata,
        Column('id', String(length=16), primary_key=True),
        Column('zoom', Integer),
        Column('lonMap', Float),
        Column('latMap', Float),
        Column('lonStart', Float),
        Column('latStart', Float),
        Column('lonDest', Float),
        Column('latDest', Float),
        Column('addressStart', Text),
        Column('addressDest', Text),
        Column('chrone', DateTime(timezone=False)),
        Column('s_node', Integer),
        Column('d_node', Integer),
        )
        self.metadata.create_all()
        mapper(HUrl, self.hash_table)

    def addRouteToDatabase(self,lonMap,latMap,zoom,lonStart,latStart,lonDest,latDest,addressStart,addressDest,nodeStart,nodeDest):
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
	h.update(str(nodeStart))
	h.update(str(nodeDest))
        h.update(str(chrone).encode("utf-8"))
        self.session.add( HUrl( h.hexdigest()[0:16], zoom, lonMap, latMap, lonStart, latStart, lonDest, latDest, addressStart, addressDest, chrone, nodeStart, nodeDest) )
        self.session.commit()
        return h.hexdigest()[0:16]

    def getDataFromHash(self,value):
        ver = session.query(HUrl).filter(HUrl.id == value).count()
        if( ver == 0 ):
            return []
        else:
             tmp = session.query(HUrl).filter(HUrl.id == value)
             for u in tmp:
                 res = []
                 res.append( u.id )
                 res.append( u.zoom )
                 res.append( u.lonMap )
                 res.append( u.latMap )
                 res.append( u.lonStart )
                 res.append( u.latStart )
                 res.append( u.lonDest )
                 res.append( u.latDest )
                 res.append( u.addressStart )
                 res.append( u.addressDest )
                 res.append( u.s_node )
                 res.append( u.d_node )
                 return res


class HUrl(object):
        def __init__(self, id, zoom, lonMap, latMap, lonStart, latStart, lonDest, latDest, addressStart, addressDest, chrone, s_node, d_node):
            self.id = id
            self.zoom = zoom
            self.lonMap = lonMap
            self.latMap = latMap
            self.lonStart = lonStart
            self.latStart = latStart
            self.lonDest = lonDest
            self.latDest = latDest
            self.addressStart = addressStart
            self.addressDest = addressDest
            self.chrone = chrone
            self.s_node = s_node
            self.d_node = d_node
   
        def __repr__(self):
            return "<hurl('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')>" % (self.id, self.zoom, self.lonMap, self.latMap,self.lonStart, self.latStart, self.lonDest, self.latDest,self.addressStart, self.addressDest, self.chrone, self.s_node, self.d_node)

#if __name__ == "__main__":
#    engine = create_engine('sqlite:////home/ody/takis.db')
#    metadata = MetaData(bind = engine)
#    Session = sessionmaker(bind=engine)
#    session = Session()
#    v = shortURL(metadata,session)
#    print v.getDataFromHash('f337af39b53fe109')
    #v.addRouteToDatabase(1.46,48.3,15,6.22,65.33,43.21,43.11,'Takis the cat','Toulouse clemence',12,2343)
#    v.import_data()
#    v.update_from_db()    
#    print v.to_string()
#    print "Done!"

