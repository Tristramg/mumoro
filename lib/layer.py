import mumoro
import psycopg2 as pg
import sqlite3

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


class Layer:
    def __init__(self, name, mode, data):
        self.mode = mode
        self.data = data
        self.name = name
        try:
            self.conn = pg.connect("dbname='mumoro' user='tristram'");
        except:
            print "I am unable to connect to the database"
        self.nodes_offset = 0

        self.nodes_db = sqlite3.connect(':memory:', check_same_thread = False)
        self.nodes_db.executescript('''
                CREATE TABLE nodes(
                    osm_id INTEGER PRIMARY KEY,
                    id INTEGER,
                    lon REAL,
                    lat REAL
                );
                CREATE INDEX lon_lat_idx ON nodes(lon, lat);
                CREATE INDEX id_idx ON nodes(id);
                ''')
        nodes_cur = self.conn.cursor()
        nodes_cur.execute('SELECT id, st_x(the_geom) as lon, st_y(the_geom) as lat FROM {0}'.format(data['nodes']))
        self.count = 0
        for n in nodes_cur:
            self.nodes_db.execute('INSERT into nodes (id, osm_id, lon, lat) VALUES(?, ?, ?, ?)', (self.count, n[0], n[1], n[2]))
            self.count += 1
        self.nodes_db.commit()
               
    def map(self, osm_node_id):
        c = self.nodes_db.cursor()
        c.execute('SELECT id FROM nodes WHERE osm_id=?', (osm_node_id,))
        row = c.fetchone()
        if row:
            return int(row[0]) + self.offset
        else:
            print osm_node_id
        
    def edges(self):
        edges_cur = self.conn.cursor()
        edges_cur.execute('SELECT source, target, length, car, car_rev, bike, bike_rev, foot from {0}'.format(self.data['edges']))
        for edge in edges_cur:
            e = mumoro.Edge()
            e.nb_changes = 0
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

            try:
                dur = duration(e.length, property, self.mode)
                e.duration = mumoro.Duration(dur)
                yield {
                    'source': int(edge[0]),
                    'target': int(edge[1]),
                    'properties': e
                    }
            except NotAccessible:
                pass

            try:
                dur = duration(e.length, property_rev, self.mode)
                e.duration = mumoro.Duration(dur)
                yield {
                    'source': int(edge[1]),
                    'target': int(edge[0]),
                    'properties': e,
                    }
            except NotAccessible:
                pass

    def match(self, lon, lat):
        epsilon = 0.001
        query =  "SELECT id FROM nodes WHERE lon >= ? AND lon <= ? AND lat >= ? AND lat <= ? ORDER BY (lon-?)*(lon-?) + (lat-?) * (lat-?) LIMIT 1"
        cur = self.nodes_db.cursor()
        cur.execute(query, (float(lon) - epsilon, float(lon) + epsilon, float(lat) - epsilon, float(lat) + epsilon, lon, lon, lat, lat))
        row = cur.fetchone()
        if row:
            return row[0]

    def coordinates(self, node):
        query = "SELECT lon, lat, osm_id FROM nodes WHERE id=?"
        cur = self.nodes_db.cursor()
        cur.execute(query, (node - self.offset,))
        row = cur.fetchone()
        if row:
            return (row[0], row[1], row[2])


class MultimodalGraph:
    def __init__(self, layers):
        nb_nodes = 0
        self.node_to_layer = []
        self.layers = layers
        for l in layers:
            self.node_to_layer.append((nb_nodes, l.name))
            l.offset = nb_nodes
            nb_nodes += l.count

        self.graph = mumoro.Graph(nb_nodes)

        count = 0
        for l in layers:
            for e in l.edges():
                self.graph.add_edge(l.map(e['source']), l.map(e['target']), e['properties'])
                count += 1
        print count


    def layer(self, node):
        for l in self.node_to_layer:
            if int(node) > l[0]:
                return l[1]
        print "Unable to find the right layer for node {0}".format(node)
        print self.node_to_layer

    def coordinates(self, node):
        name = self.layer(node)
        for l in self.layers:
            if l.name == name:
                return l.coordinates(node)

    def match(self, name, lon, lat):
        for l in self.layers:
            if l.name == name:
                return l.match(lon, lat)

    def connect_same_nodes(self, layer1, layer2):
        for n in layer1.nodes():
            pass

