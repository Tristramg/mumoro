import core.mumoro as mumoro
#import psycopg2 as pg
import sqlite3
import elevation
import math

from sqlalchemy import *
from sqlalchemy.orm import *
 
class NotAccessible(Exception):
    pass
 
def duration(length, property, mode):
    if mode == mumoro.Foot:
        if property == 0:
            raise NotAccessible()
        else:
            return length * 3.6 / 5
    elif mode == mumoro.Bike:
        if property == 0:
            raise NotAccessible()
        else:
            return length * 3.6 / 15
    elif mode == mumoro.Car:
        if property == 1:
            return length * 3.6 / 15
        elif property == 2:
            return length * 3.6 / 20
        elif property == 3:
            return length * 3.6 / 30
        elif property == 4:
            return length * 3.6 / 70
        elif property == 5:
            return length * 3.6 / 80
        elif property == 6:
            return length * 3.6 / 100
        else:
            raise NotAccessible()
    else:
        raise NotAccessible()
 
class BaseLayer:
    class Node(object):
        def __init__(self, id, lon, lat, the_geom):
            self.id = id
            self.lon = lon
            self.lat = lat
            self.the_geom = the_geom
   
        def __repr__(self):
            return "<Node('%s','%s', '%s', '%s')>" % (self.id, self.lon, self.lat, self.the_geom)

    class Edge(object):
        def __init__(self, id, source, target, length, car, car_rev, bike, bike_rev, foot, the_geom):
            self.id = id
            self.source = source
            self.target = target
            self.length = length
            self.car = car
            self.car_rev = car_rev
            self.bike = bike
            self.bike_rev = bike_rev
            self.foot = foot
            self.the_geom = the_geom

        def __repr__(self):
            return "<Edge('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')>" % (self.id, self.source, self.target, self.length,self.car, self.car_rev, self.bike, self.bike_rev,self.foot, self.the_geom)

    def __init__(self):
        self.engine = create_engine('sqlite:///db_test.db', echo=True)
        self.metadata = MetaData()
        mapper(Node, self.nodes_table)
        mapper(Edge, self.edges_table)
        

    def map(self, o_id):
        Session = sessionmaker(bind=self.engine)
        self.session = Session()        
        #c = self.nodes_db.cursor()
        #c.execute('SELECT id FROM nodes WHERE original_id=?', (original_id,))
        #row = c.fetchone()
        try:        
                row = self.session.query(Node.id).filter_by(original_id=o_id).one()
                return int(row[0]) + self.offset   
        except NoResultFound, e:
                print "Unable to find id {0}".format(o_id)
        
 
    def match(self, ln, lt):
        epsilon = 0.002
        Session = sessionmaker(bind=self.engine)
        self.session = Session()        
        #query = "SELECT id FROM nodes WHERE lon >= ? AND lon <= ? AND lat >= ? AND lat <= ? ORDER BY (lon-?)*(lon-?) + (lat-?) * (lat-?) LIMIT 1"
        #cur = self.nodes_db.cursor()
        #cur.execute(query, (float(lon) - epsilon, float(lon) + epsilon, float(lat) - epsilon, float(lat) + epsilon, lon, lon, lat, lat))
        #row = cur.fetchone()
        try:        
                row = self.session.query(Node.id).filter_by(lon>=float(ln)-epsilon).filter_by(lon<=float(ln)+epsilon).filter_by(lat>=float(lt)-epsilon).filter_by(lat<=float(lt)+epsilon).order_by((Node.lon-ln)*(Node.lon-ln)+(Node.lat-lt)*(Node.lat-lt)).one()[1]
                return int(row[0]) + self.offset   
        except NoResultFound, e:
                print "Unable to find id {0}".format(o_id)        

 
    def coordinates(self, nd):
        #query = "SELECT lon, lat, original_id, network FROM nodes WHERE id=?"
        #cur = self.nodes_db.cursor()
        #cur.execute(query, (node - self.offset,))
        #row = cur.fetchone()
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        res = self.session.query(Node.lon,Node.lat,Node.original_id).filter_by(Node.id=nd)    
        if res.network == "osm":
            network = self.name
        else:
            network = res.network      
        if res:
            return (res.lon, res.lat, res.original_id, network)
        else:
            print "Unknow node {0} on layer {1}".format(nd, self.name)
 
    def nodes(self):
        #query = "SELECT id, original_id, lon, lat FROM nodes"
        #cur = self.nodes_db.cursor()
        #cur.execute(query)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
               
        for row in self.session.query(Node.id,Node.original_id,Node.lon,Node.lat):
            yield {
                    'id': int(row.id) + self.offset,
                    'original_id': row.original_id,
                    'lon': float(row.lon),
                    'lat': float(row.lat)
                    }
 
 
class Layer(BaseLayer):
    def __init__(self, name, mode, data, c):
        self.mode = mode
        self.data = data
        self.name = name
        	
        #try:
        #    if( c.host != "" and c.dbpassword != ""):
        #        self.conn = pg.connect("dbname=" + c.dbname + " user=" + c.dbuser  + " password=" + c.dbpassword + " host=" + c.host)
        #    else:
        #        self.conn = pg.connect("dbname=" + c.dbname + " user=" + c.dbuser)
        #except:
        #    print "I am unable to connect to the database"
        self.nodes_offset = 0
	eld = elevation.ElevationData("Eurasia")
	self.nodes_db = sqlite3.connect(':memory:', check_same_thread = False)
	self.nodes_db.executescript('''
CREATE TABLE nodes(
original_id INTEGER PRIMARY KEY,
id INTEGER,
lon REAL,
lat REAL,
alt REAL,
network TEXT
);
CREATE INDEX lon_lat_idx ON nodes(lon, lat);
CREATE INDEX id_idx ON nodes(id);
CREATE INDEX original_idx ON nodes(original_id);
''')
        nodes_cur = self.conn.cursor()
        ##nodes_cur.execute('SELECT id, st_x(the_geom) as lon, st_y(the_geom) as lat FROM {0}'.format(data['nodes']))
        nodes_cur.execute('SELECT id, lon, lat FROM {0}'.format(data['nodes']))
        self.count = 0
        for n in nodes_cur:
            alt = eld.altitude(n[2], n[1])
            self.nodes_db.execute('INSERT into nodes (id, original_id, lon, lat, network, alt) VALUES(?, ?, ?, ?, "osm", ?)', (self.count, n[0], n[1], n[2], alt))
            self.count += 1
        print "Layer {0} loaded with {1} nodes".format(name, self.count)
               
    def edges(self):
        nodes_cur = self.nodes_db.cursor()
        edges_cur = self.conn.cursor()
        edges_cur.execute('SELECT source, target, length, car, car_rev, bike, bike_rev, foot from {0}'.format(self.data['edges']))
        for edge in edges_cur:
            nodes_cur.execute('SELECT alt FROM nodes WHERE original_id=?', (edge[0],))
            source_alt = int(nodes_cur.fetchone()[0])
            nodes_cur.execute('SELECT alt FROM nodes WHERE original_id=?', (edge[1],))
            target_alt = int(nodes_cur.fetchone()[0])
            e = mumoro.Edge()
            e.length = float(edge[2])
            if self.mode == mumoro.Foot:
                property = int(edge[7])
                property_rev = int(edge[7])
            elif self.mode == mumoro.Bike:
                property = int(edge[5])
                property_rev = int(edge[6])
            elif self.mode == mumoro.Car:
                property = int(edge[3])
                property_rev = int(edge[4])
            else:
                property = 0
                property_rev = 0
 
            node1 = self.map(edge[0])
            node2 = self.map(edge[1])
 
            try:
                dur = duration(e.length, property, self.mode)
                e.duration = mumoro.Duration(dur)
                if self.mode == mumoro.Bike:
                    e.elevation = max(0, target_alt - source_alt)
                yield {
                    'source': node1,
                    'target': node2,
                    'properties': e
                    }
            except NotAccessible:
                pass
 
            try:
                dur = duration(e.length, property_rev, self.mode)
                e.duration = mumoro.Duration(dur)
                if self.mode == mumoro.Bike:
                    e.elevation = max(0, source_alt - target_alt)
                yield {
                    'source': node2,
                    'target': node1,
                    'properties': e,
                    }
            except NotAccessible:
                pass
 
    
 
class GTFSLayer(BaseLayer):
    def __init__(self, name, data):
        Session = sessionmaker(bind=self.engine)
        self.session = Session()        
        #self.nodes_db = sqlite3.connect(data, check_same_thread = False)
        #c = self.nodes_db.cursor()
        #c.execute("SELECT count(1) FROM nodes")
        self.count = self.session.query(Node).count()        
        #self.count = int(c.fetchone()[0])
        self.offset = 0
        self.name = name
        print "Layer {0} loaded with {1} nodes".format(name, self.count)
 
    def edges(self):
        Session = sessionmaker(bind=self.engine)
        self.session = Session()        
        #c = self.nodes_db.cursor()
        #c.execute("SELECT source, target, start_secs, arrival_secs FROM edges")
        for row in self.session.query(Edges.source,Edges.target,Edges.start_secs,Edges.arrival_secs):
            yield {
                    'source': row.source + self.offset,
                    'target': row.target + self.offset,
                    'departure': row.start_secs,
                    'arrival': row.arrival_secs
                    }
 
        # Connects every node corresponding to a same stop:
        # if a stop is used by 3 routes, the stop will be represented by 3 nodes
        #c.execute("SELECT n1.id, n2.id FROM nodes as n1, nodes as n2 WHERE n1.original_id = n2.original_id AND n1.route <> n2.route")
        e = mumoro.Edge()
        e.line_change = 1
        e.duration = mumoro.Duration(60) # There should be at least a minute between two bus/trains at the same station
        #for row in self.session.query(Edges.source,Edges.target,Edges.start_secs,Edges.arrival_secs):# Didn't find yet how to name colums in a 
        #    yield {                                                                                  # query with sqlalchemy
        #            'source': row[0] + self.offset,    
        #            'target': row[1] + self.offset,
        #            'properties': e
        #            }
 
class MultimodalGraph:
    def __init__(self, layers):
        nb_nodes = 0
        self.node_to_layer = []
        self.layers = layers
        for l in layers:
            l.offset = nb_nodes
            nb_nodes += l.count
            self.node_to_layer.append((nb_nodes, l.name))
 
        self.graph = mumoro.Graph(nb_nodes)
 
        count = 0
        for l in layers:
            for e in l.edges():
                if e.has_key('properties'):
                    self.graph.add_edge(e['source'], e['target'], e['properties'])
                    count += 1
                else:
                    if self.graph.public_transport_edge(e['source'], e['target'], e['departure'], e['arrival']):
                        count += 1
	    print "On layer {0}, {1} edges".format(l, count)
        print "The multimodal graph has been built and has {0} nodes and {1} edges".format(nb_nodes, count)
 
 
    def layer(self, node):
        for l in self.node_to_layer:
            if int(node) < l[0]:
                return l[1]
        print "Unable to find the right layer for node {0}".format(node)
        print self.node_to_layer
 
    def coordinates(self, node):
        name = self.layer(node)
        for l in self.layers:
            if l.name == name:
                return l.coordinates(node)
        print "Unknown node: {0} on layer: {1}".format(node, name)
 
    def match(self, name, lon, lat):
        for l in self.layers:
            if l.name == name:
                return l.match(lon, lat)

    def distance(self, n1, n2):
        c1 = self.coordinates(n1)
        c2 = self.coordinates(n2)
        try:
            delta = c2[0] - c1[0]
            a = math.radians(c1[1])
            b = math.radians(c2[1])
            C = math.radians(delta)
            x = math.sin(a) * math.sin(b) + math.cos(a) * math.cos(b) * math.cos(C)
            distance = math.acos(x) # in radians
            distance  = math.degrees(distance) # in degrees
            distance  = distance * 60 # 60 nautical miles / lat degree
            distance = distance * 1852 # conversion to meters
            return distance;
        except:
            return 0

 
    def connect_same_nodes(self, layer1, layer2, property):
        for n1 in layer1.nodes():
            n2 = layer2.map(n1['original_id'])
            if n2:
                self.graph.add_edge(n1['id'], n2, property)

    def connect_same_nodes_random(self, layer1, layer2, property, freq):
        count = 0
        for n1 in layer1.nodes():
            n2 = layer2.map(n1['original_id'])
            count += 1
            if n2 and count % freq == 0:
                self.graph.add_edge(n1['id'], n2, property)


    def connect_nodes_from_list(self, layer1, layer2, list, property, property2 = None):
        if property2 == None:
            property2 = property
        for coord in list:
            n1 = layer1.match(coord['lon'], coord['lat'])
            n2 = layer2.match(coord['lon'], coord['lat'])
            if n1 and n2:
                self.graph.add_edge(n1, n2, property)
                self.graph.add_edge(n2, n1, property2)
            else:
                print "Uho... no connection possible"


    def connect_nearest_nodes(self, layer1, layer2, property, property2 = None):
        if property2 == None:
            property2 = property
        for n in layer1.nodes():
            nearest = layer2.match(n['lon'], n['lat'])
            if nearest:
                self.graph.add_edge(n['id'], nearest, property)
                self.graph.add_edge(nearest, n['id'], property2)



 
