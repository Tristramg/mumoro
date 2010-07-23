from sqlalchemy import *

class Metadata(object):
    def __init__(self, name, node_or_edge, origin):
        self.name = name
        self.node_or_edge = node_or_edge
        self.origin = origin

class Node(object):
    def __init__(self, id, lon, lat, the_geom = ""):
        self.original_id = id
        self.lon = lon
        self.lat = lat
        self.the_geom = the_geom

class PT_Node(object):
    def __init__(self, id, lon, lat, route, the_geom = ""):
        self.original_id = id
        self.lon = lon
        self.lat = lat
        self.route = route
        self.the_geom = the_geom

class PT_Service(object):
    def __init__(self, id, services):
        self.id = id
        self.services = services

class Edge(object):
    def __init__(self, id, source, target, length, car, car_rev, bike, bike_rev, foot, the_geom = ""):
        self.original_id = id
        self.source = source
        self.target = target
        self.length = length
        self.car = car
        self.car_rev = car_rev
        self.bike = bike
        self.bike_rev = bike_rev
        self.foot = foot
        self.the_geom = the_geom

class PT_Edge(object):
    def __init__(self, source, target, length, start_secs, arrival_secs, services, mode):
        self.source = source
        self.target = target
        self.length = length
        self.start_secs = start_secs
        self.arrival_secs = arrival_secs
        self.services = services
        self.mode = mode

def create_nodes_table(id, metadata):
    table = Table(id, metadata, 
            Column('id', Integer, primary_key = True),
            Column('original_id', String, index = True),
            Column('elevation', Integer),
            Column('lon', Float, index = True),
            Column('lat', Float, index = True),
            Column('the_geom', String),
            )
    metadata.create_all()
    return table

def create_pt_nodes_table(id, metadata):
    table = Table(id, metadata, 
            Column('id', Integer, primary_key = True),
            Column('original_id', String, index = True),
            Column('lon', Float, index = True),
            Column('lat', Float),
            Column('the_geom', String),
            Column('route', String)
            )
    metadata.create_all()
    return table

def create_services_table(id, metadata):
    table = Table(id, metadata,
            Column('id', Integer, primary_key = True),
            Column('services', String)
            )
    metadata.create_all()
    return table

def create_edges_table(id, metadata):
    table = Table(id, metadata,
            Column('id', Integer, primary_key = True),
            Column('source', Integer, index = True),
            Column('target', Integer, index = True),
            Column('length', Float),
            Column('car', Integer),
            Column('car_rev', Integer),
            Column('bike', Integer),
            Column('bike_rev', Integer),
            Column('foot', Integer),
            Column('the_geom', String),
            )
    metadata.create_all()
    return table
            
def create_pt_edges_table(id, metadata, services_table):
    table = Table(id, metadata,
            Column('id', Integer, primary_key = True),
            Column('source', Integer, index = True),
            Column('target', Integer, index = True),
            Column('length', Float),
            Column('start_secs', Integer),
            Column('arrival_secs', Integer),
            Column('services', Integer,  ForeignKey(services_table + ".id")),
            Column('mode', Integer),
            )
    metadata.create_all()
    return table


