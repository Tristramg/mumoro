import mumoro
import psycopg2 as pg
import sqlite3
import elevation

 
class NotAccessible(Exception):
    pass
 
def duration(length, property, mode):
    if mode == mumoro.Foot:
        if property == 0:
            raise NotAccessible()
        else:
            return 5 * length / 3.5
    elif mode == mumoro.Bike:
        if property == 0:
            raise NotAccessible()
        else:
            return length / 4.2
    elif mode == mumoro.Car:
        if property == 1:
            return 20 * length / 3.6
        elif property == 2:
            return 30 * length / 3.6
        elif property == 3:
            return 50 * length / 3.6
        elif property == 4:
            return 90 * length / 3.6
        elif property == 5:
            return 100 * length / 3.6
        elif property == 6:
            return 120 * length / 3.6
        else:
            raise NotAccessible()
    else:
        raise NotAccessible()
 
class BaseLayer:
    def map(self, original_id):
        c = self.nodes_db.cursor()
        c.execute('SELECT id FROM nodes WHERE original_id=?', (original_id,))
        row = c.fetchone()
        if row:
            return int(row[0]) + self.offset
        else:
            print "Unable to find id {0}".format(original_id)
 
    def match(self, lon, lat):
        epsilon = 0.001
        query = "SELECT id FROM nodes WHERE lon >= ? AND lon <= ? AND lat >= ? AND lat <= ? ORDER BY (lon-?)*(lon-?) + (lat-?) * (lat-?) LIMIT 1"
        cur = self.nodes_db.cursor()
        cur.execute(query, (float(lon) - epsilon, float(lon) + epsilon, float(lat) - epsilon, float(lat) + epsilon, lon, lon, lat, lat))
        row = cur.fetchone()
        if row:
            return int(row[0]) + self.offset
 
    def coordinates(self, node):
        query = "SELECT lon, lat, original_id, network FROM nodes WHERE id=?"
        cur = self.nodes_db.cursor()
        cur.execute(query, (node - self.offset,))
        row = cur.fetchone()
        if row[3] == "osm":
            network = self.name
        else:
            network = row[3]
        if row:
            return (row[0], row[1], row[2], network)
        else:
            print "Unknow node {0} on layer {1}".format(node, self.name)
 
    def nodes(self):
        query = "SELECT id, original_id, lon, lat FROM nodes"
        cur = self.nodes_db.cursor()
        cur.execute(query)
        for row in cur:
            yield {
                    'id': int(row[0]) + self.offset,
                    'original_id': row[1],
                    'lon': float(row[2]),
                    'lat': float(row[3])
                    }
 
 
class Layer(BaseLayer):
    def __init__(self, name, mode, data):
        self.mode = mode
        self.data = data
        self.name = name
        try:
            self.conn = pg.connect("dbname='mumoro'");
        except:
            print "I am unable to connect to the database"
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
        #nodes_cur.execute('SELECT id, st_x(the_geom) as lon, st_y(the_geom) as lat FROM {0}'.format(data['nodes']))
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
        self.nodes_db = sqlite3.connect(data, check_same_thread = False)
        c = self.nodes_db.cursor()
        c.execute("SELECT count(1) FROM nodes")
        self.count = int(c.fetchone()[0])
        self.offset = 0
        self.name = name
        print "Layer {0} loaded with {1} nodes".format(name, self.count)
 
    def edges(self):
        c = self.nodes_db.cursor()
        c.execute("SELECT source, target, start_secs, arrival_secs FROM edges")
        for row in c:
            yield {
                    'source': row[0] + self.offset,
                    'target': row[1] + self.offset,
                    'departure': row[2],
                    'arrival': row[3]
                    }
 
        # Connects every node corresponding to a same stop:
        # if a stop is used by 3 routes, the stop will be represented by 3 nodes
        c.execute("SELECT n1.id, n2.id FROM nodes as n1, nodes as n2 WHERE n1.original_id = n2.original_id AND n1.route <> n2.route")
        e = mumoro.Edge()
        e.line_change = 1
        e.duration = mumoro.Duration(60) # There should be at least a minute between two bus/trains at the same station
        for row in c:
            yield {
                    'source': row[0] + self.offset,
                    'target': row[1] + self.offset,
                    'properties': e
                    }
 
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
 
    def connect_same_nodes(self, layer1, layer2, property):
        for n1 in layer1.nodes():
            n2 = layer2.map(n1['original_id'])
            if n2:
                self.graph.add_edge(n1, n2, property)


    def connect_nodes_from_list(self, layer1, layer2, list, property, property2 = None):
        if property2 == None:
            property2 = property
        for coord in list:
            n1 = layer1.match(coord['lon'], coord['lat'])
            n2 = layer2.match(coord['lon'], coord['lat'])
            if n1 and n2:
                self.graph.add_edge(n1, n2, property)
                self.graph.add_edge(n2, n1, property2)
                print "edge added"
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
 
