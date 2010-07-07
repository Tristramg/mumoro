from lib.datastructures import *
import core.mumoro as mumoro

from sqlalchemy import *
from sqlalchemy.orm import *
 
class NotAccessible(Exception):
    pass

class DataIncoherence(Exception):
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

    def map(self, o_id):
        result = self.nodes_table.select(self.nodes_table.c.original_id==o_id).execute().first()
        if result:
            return result.id
        else:
            print "Unable to find id {0}".format(o_id)
            raise DataIncoherence()
        
 
    def match(self, ln, lt):
        epsilon = 0.002
        ln = float(ln)
        lt = float(lt)
        res = self.nodes_table.select(
                (self.nodes_table.c.lon >= (ln - epsilon)) &
                (self.nodes_table.c.lon <= (ln + epsilon)) &
                (self.nodes_table.c.lat >= (lt - epsilon)) &
                (self.nodes_table.c.lat <= (lt + epsilon)),
                order_by = ((self.nodes_table.c.lon - ln) * (self.nodes_table.c.lon -ln)) + ((self.nodes_table.c.lat - lt) * (self.nodes_table.c.lat - lt))
                ).execute().first()
            
        if res:
            return res.id + self.offset
        else:
            print "Unable to find id {0}".format(o_id)        

 
    def coordinates(self, nd):
        res = self.nodes_table.select(self.nodes_table.c.id == nd).execute().first()    
        if res:
            return (res.lon, res.lat, res.original_id, self.name)
        else:
            print "Unknow node {0} on layer {1}".format(nd, self.name)
 
    def nodes(self):
        for row in self.nodes_table.select().execute():
            yield {
                    'id': int(row.id) + self.offset,
                    'original_id': row.original_id,
                    'lon': float(row.lon),
                    'lat': float(row.lat)
                    }
 
 
class Layer(BaseLayer):
    def __init__(self, name, mode, data, metadata):
        self.mode = mode
        self.data = data
        self.name = name
        self.metadata = metadata
        self.nodes_table = Table(data['nodes'], metadata, autoload = True)
        self.edges_table = Table(data['edges'], metadata, autoload = True)
        self.count = select([func.count(self.nodes_table.c.id)]).execute().first()[0]

               
    def edges(self):
        for edge in self.edges_table.select().execute():
            e = mumoro.Edge()
            e.length = edge.length
            if self.mode == mumoro.Foot:
                property = edge.foot
                property_rev = edge.foot
            elif self.mode == mumoro.Bike:
                property = edge.bike
                property_rev = edge.bike_rev
            elif self.mode == mumoro.Car:
                property = edge.car
                property_rev = edge.car_rev
            else:
                property = 0
                property_rev = 0
 
            node1 = self.map(edge.source)
            node2 = self.map(edge.target)
 
            try:
                dur = duration(e.length, property, self.mode)
                e.duration = mumoro.Duration(dur)
                e.elevation = 0
              #  if self.mode == mumoro.Bike:
              #      e.elevation = max(0, target_alt - source_alt)
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
                e.elevation = 0
#                if self.mode == mumoro.Bike:
#                    e.elevation = max(0, source_alt - target_alt)
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
    def __init__(self, layers, filename = None):
        nb_nodes = 0
        self.node_to_layer = []
        self.layers = layers
        for l in layers:
            l.offset = nb_nodes
            nb_nodes += l.count
            self.node_to_layer.append((nb_nodes, l.name))
 
        self.graph = mumoro.Graph(nb_nodes)
 
        if filename:
            self.graph = mumoro.Graph(filename)
        else:
            count = 0
            for l in layers:
                for e in l.edges():
                    if e.has_key('properties'):
                        self.graph.add_edge(e['source'], e['target'], e['properties'])
                        count += 1
                    else:
                        if self.graph.public_transport_edge(e['source'], e['target'], e['departure'], e['arrival']):
                            count += 1
                print "On layer {0}, {1} edges, {2} nodes".format(l.name, count, l.count)
            print "The multimodal graph has been built and has {0} nodes and {1} edges".format(nb_nodes, count)
 
    def save(self, filename):
        self.graph.save(filename)

    def load(self, filename):
        self.graph.save(filename)
 
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
        count = 0
        for n1 in layer1.nodes():
            n2 = layer2.map(n1['original_id'])
            if n2:
                self.graph.add_edge(n1['id'], n2, property)
                count += 1
        return count

    def connect_same_nodes_random(self, layer1, layer2, property, freq):
        count = 0
        for n1 in layer1.nodes():
            n2 = layer2.map(n1['original_id'])
            if n2 and count % freq == 0:
                self.graph.add_edge(n1['id'], n2, property)
                count += 1
        return count


    def connect_nodes_from_list(self, layer1, layer2, list, property, property2 = None):
        count = 0
        if property2 == None:
            property2 = property
        for coord in list:
            n1 = layer1.match(coord['lon'], coord['lat'])
            n2 = layer2.match(coord['lon'], coord['lat'])
            if n1 and n2:
                self.graph.add_edge(n1, n2, property)
                self.graph.add_edge(n2, n1, property2)
                count += 2
            else:
                print "Uho... no connection possible"
        return count


    def connect_nearest_nodes(self, layer1, layer2, property, property2 = None):
        count = 0
        if property2 == None:
            property2 = property
        for n in layer1.nodes():
            nearest = layer2.match(n['lon'], n['lat'])
            if nearest:
                self.graph.add_edge(n['id'], nearest, property)
                self.graph.add_edge(nearest, n['id'], property2)
                count += 2
        return count
 
