# -*- coding: utf-8 -*-

import hashlib
import string
import config
import time

from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.dialects.postgresql.base import *

class shortURL:
    def __init__(self):
        self.engine = create_engine('sqlite:///db_test.db', echo=True)
        self.metadata = MetaData()

        self.hash_table = Table('hurl', self.metadata,
        Column('id', String(length=16), primary_key=True),
        Column('zoom', Integer),
        Column('lonMap', DOUBLE_PRECISION),
        Column('latMap', DOUBLE_PRECISION),
        Column('lonStart', DOUBLE_PRECISION),
        Column('latStart', DOUBLE_PRECISION),
        Column('lonDest', DOUBLE_PRECISION),
        Column('latDest', DOUBLE_PRECISION),
        Column('addressStart', Text),
        Column('addressDest', Text),
        Column('chrone', TIMESTAMP(timezone=False)),
        Column('s_node', Integer),
        Column('d_node', Integer),
        )
        self.metadata.create_all(self.engine)
        mapper(HUrl, self.hash_Table)

    def addRouteToDatabase(self,lonMap,latMap,zoom,lonStart,latStart,lonDest,latDest,addressStart,addressDest,nodeStart,nodeDest):
        h = hashlib.md5()
	chrone = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())        
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
        h.update(chrone.encode("utf-8"))
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.session.add( HUrl( h.hexdigest()[0:16], zoom, lonMap, latMap, lonStart, latStart, lonDest, latDest, addressStart, addressDest, chrone, nodeStart, nodeDest) )
        self.session.commit()
        return h.hexdigest()[0:16]

    def getDataFromHash(self,value):
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        ver = session.query(HUrl).filter(HUrl.id == value).count()
        if( ver == 0 ):
            return []
        else:
            tmp = session.query(HUrl).filter(HUrl.id == value)
            return tmp


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

