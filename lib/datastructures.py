class Metadata(object):
    def __init__(self, name, origin):
        self.name = name
        self.origin = origin

class Node(object):
    def __init__(self, id, lon, lat, the_geom = ""):
        self.original_id = id
        self.lon = lon
        self.lat = lat
        self.the_geom = the_geom

class PT_Node(object):
    def __init__(self, original_id, lon, lat, route, the_geom = ""):
        self.orginal_id = id
        self.lon = lon
        self.lat = lat
        self.route = route
        self.the_geom = the_geom

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
    def __init__(self, id, source, target, length, start_secs, arrival_secs, mode):
        self.original_id = id
        self.source = source
        self.target = target
        self.length = length
        self.start_secs = start_secs
        self.arrival_secs = arrival_secs
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
    return table
            
def create_pt_edges_table(id, metadata):
    table = Table(id, metadata,
            Column('id', Integer, primary_key = True),
            Column('source', Integer, index = True),
            Column('target', Integer, index = True),
            Column('length', Float),
            Column('start_secs', Integer),
            Column('arrival_secs', Integer),
            Column('services', String),
            Column('mode', Integer)
            )
    return table


