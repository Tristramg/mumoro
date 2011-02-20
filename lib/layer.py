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
#    © Demotera 2011
#    Author: Paul Rivier, Pierre Paysant-Le Roux


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
            return length * 3.6 / 12
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
 
class BaseLayer(object):
    def __init__(self, name, data, metadata):
        self.data = data
        self.name = name
        self.metadata = metadata
        self.nodes_table = Table(data['nodes'], metadata, autoload = True)
        self.edges_table = Table(data['edges'], metadata, autoload = True)
        self.count = select([func.count(self.nodes_table.c.id)]).execute().first()[0]

    def map(self, o_id):
        s = self.nodes_table.select(self.nodes_table.c.original_id==o_id)
        rs = s.execute()
        for row in rs:
            result = row
        if result:
            return result[0] + self.offset
        else:
            print "Unable to find id {0}".format(o_id)
            raise DataIncoherence()

    def borders(self):
        max_lon = select([func.max(self.nodes_table.c.lon, type_=Float )]).execute().first()[0]    
        min_lon = select([func.min(self.nodes_table.c.lon, type_=Float )]).execute().first()[0]
        max_lat = select([func.max(self.nodes_table.c.lat, type_=Float )]).execute().first()[0]    
        min_lat = select([func.min(self.nodes_table.c.lat, type_=Float )]).execute().first()[0]
        return {'max_lon': max_lon,'min_lon': min_lon,'max_lat':max_lat,'min_lat':min_lat}

    def average(self):
        avg_lon = select([func.avg(self.nodes_table.c.lon, type_=Float )]).execute().first()[0]    
        avg_lat = select([func.avg(self.nodes_table.c.lat, type_=Float )]).execute().first()[0]
        return {'avg_lon':avg_lon, 'avg_lat':avg_lat }
 
    def match(self, ln, lt, epsilon = 0.002):
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
            return None

 
    def node(self, nd):
        res = self.nodes_table.select(self.nodes_table.c.id == (nd - self.offset)).execute().first()
        if res:
            return res
        else:
            print "Unknow node {0} on layer {1}, offset ".format(nd, self.name, self.offset)


    def coordinates(self, nd):
        res = self.node(nd)
        return (res.lon, res.lat, res.original_id, self.name)
 
    def nodes(self):
        for row in self.nodes_table.select().execute():
            yield row  
 
class Layer(BaseLayer):
    def __init__(self, name, mode, data, metadata, bike_service=None):
        super(Layer, self).__init__(name, data, metadata)
        self.mode = mode
        self.bike_service = bike_service
               
    def edges(self):
        for edge in self.edges_table.select().execute():
            # print "strange edge !"
            e = mumoro.Edge()
            e.length = edge.length
            if self.mode == mumoro.Foot:
                property = edge.foot
                property_rev = edge.foot
                e.penibility = e.length
            elif self.mode == mumoro.Bike:
                property = edge.bike
                e.penibility = e.length * 0.5
                property_rev = edge.bike_rev
            elif self.mode == mumoro.Car:
                property = edge.car
                property_rev = edge.car_rev
                e.penibility = 0
            else:
                property = 0
                property_rev = 0
                e.penibility = 0
 
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
                yield {'source': node2,
                       'target': node1,
                       'properties': e}
            except NotAccessible:
                pass
    def icon(self, node):
            if self.mode == mumoro.Foot:
                return "modes/foot.png"
            elif self.mode == mumoro.Bike:
                return "modes/bike.png"
            elif self.mode == mumoro.Car:
                return "modes/car.png"
            elif self.mod == mumoro.PublicTransport:
                return "modes/bus.png"
            else:
                return ""

    def marker_icon(self, node):
        if self.mode == mumoro.Bike:
            return 'markers/bike.png'
        else:
            return ""

    def layer_name(self):
            if self.mode == mumoro.Foot:
                return "Foot"
            elif self.mode == mumoro.Bike:
                return "Bike"
            elif self.mode == mumoro.Car:
                return "Car"
            elif self.mod == mumoro.PublicTransport:
                return "Bus"
            else:
                return ""

    def color(self, node):
        return None

    def bike_stations_table(self):
        if self.bike_service != None:
            return Table(self.bike_service['table'], self.metadata, autoload = True)
        else:
            return None

    
    def bike_station(self, node):
        if self.bike_stations_table() != None:
            t = self.bike_stations_table()
            ln = node.lon
            lt = node.lat
            epsilon = 0.002
            res = t.select(
                (t.c.lon >= (ln - epsilon)) &
                (t.c.lon <= (ln + epsilon)) &
                (t.c.lat >= (lt - epsilon)) &
                (t.c.lat <= (lt + epsilon)),
                order_by = ((t.c.lon - ln) * (t.c.lon -ln)) + ((t.c.lat - lt) * (t.c.lat - lt))
                ).execute().first()
            
            if res:
                return res
            else:
                return None
        else:
            return None

class GTFSLayer(BaseLayer):
    """A layer for public transport described by the General Transit Feed Format"""
 
    def __init__(self, name, data, metadata):
        super(GTFSLayer, self).__init__(name, data, metadata)
        self.services = Table(data['services'], metadata, autoload = True)
        self.mode = mumoro.PublicTransport
        self.stop_areas_table = Table(data['stop_areas'], metadata, autoload = True)
        self.lines_table = Table(data['lines'], metadata, autoload = True)

    def layer_name(self):
        return "Bus"

    def icon(self, node):
        return 'pictos_lignes/21/' + self.line(node).short_name + '.png'

    def color(self, node):
        color = self.line(node).color
        return "#" + (self.line(node).text_color if color == 'ffffff' else color)

    def marker_icon(self, node):
        return 'markers_lignes/' + self.line(node).short_name + '.png'

    def lines(self):
        e = self.lines_table.select().execute()
        return e

    def line(self, node):
        return self.lines_table.select(self.lines_table.c.code == str(node.route)).execute().first()

    def stop_area(self, id):
        return self.stop_areas_table.select(self.stop_areas_table.c.code == str(id)).execute().first()

    def edges(self):
        for row in self.edges_table.select().execute():
            services = self.services.select(self.services.c.id == int(row.services)).execute().first().services
            yield {'source': row.source + self.offset,
                   'target': row.target + self.offset,
                   'departure': row.start_secs,
                   'arrival': row.arrival_secs,
                   'services': services}
 
        # Connects every node corresponding to a same stop:
        # if a stop is used by 3 routes, the stop will be represented by 3 nodes
        n1 = self.nodes_table.alias()
        n2 = self.nodes_table.alias()
        res = select([n1,n2], (n1.c.original_id == n2.c.original_id) & (n1.c.route != n2.c.route)).execute()
        e = mumoro.Edge()
        e.line_change = 1
        e.duration = mumoro.Duration(60) # There should be at least a minute between two bus/trains at the same station
        e.penibility = 0
        for r in res:
            yield { 'source': r[0] + self.offset,    
                    'target': r[8] + self.offset,
                    'properties': e }
 

class MultimodalGraph(object):
    def __init__(self, layers, filename = None):
        nb_nodes = 0
        self.node_to_layer = []
        self.layers = layers
        for l in layers:
            l.offset = nb_nodes
            nb_nodes += l.count
            self.node_to_layer.append((nb_nodes, l.name))
 
        self.graph = mumoro.Graph(nb_nodes + 1) # Merci les copains d'avoir décalé tout de 1 et de m'avoir fait suer à cause d'un segfault...
 
        if filename:
            self.graph = mumoro.Graph(filename)
        else:
            count = 0
            tcount = 0
            horaires = 0
            for l in layers:
                print "Layer new"
                for e in l.edges():
                    if e.has_key('properties'):
                        self.graph.add_edge(e['source'], e['target'], e['properties'])
                        count += 1
                    else:
                        if self.graph.public_transport_edge(e['source'], e['target'], e['departure'], e['arrival'], str(e['services'])):
                            tcount += 1
                        horaires += 1
                print "On layer {0}, {1} edges, {2} transport edges, {3} nodes, {4} time events".format(l.name, count, tcount, l.count, horaires)
            self.graph.sort()
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

    def layer_object(self,node):
        name = self.layer(node)
        for l in self.layers:
            if l.name == name:
                return l
        raise NameError("Unknown node: {0} on layer: {1}".format(node, name))

    def coordinates(self, node):
        return self.layer_object(node).coordinates(node)
 
    def match(self, name, lon, lat):
        for l in self.layers:
            if l.name == name:
                return l.match(lon, lat)

 
    def connect_same_nodes(self, layer1, layer2, property):
        count = 0
        for n1 in layer1.nodes():
            n2 = layer2.map(n1.original_id)
            if n2:
                self.graph.add_edge(n1.id + layer1.offset, n2, property)
                count += 1
        return count

    def connect_same_nodes_random(self, layer1, layer2, property, freq):
        count = 0
        for n1 in layer1.nodes():
            n2 = layer2.map(n1.original_id)
            if n2 and count % freq == 0:
                self.graph.add_edge(n1.id + layer.offset, n2, property)
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
        print "Connecting nearest nodes from layer offset {0} to layer offset {1}".format(layer1.offset, layer2.offset)
        count = 0
        if property2 == None:
            property2 = property
        for n in layer1.nodes():
            nearest = layer2.match(n.lon, n.lat, 0.01)
            if nearest:
                self.graph.add_edge(n.id + layer1.offset, nearest, property)
                self.graph.add_edge(nearest, n.id + layer1.offset, property2)
                count += 2
            else:
                print "(lon='{0}' AND lat='{1}') OR".format(str(n.lon), str(n.lat))
        return count

    '''Given a vector of nodes and a departure time returns the arrival, waiting and departure time'''
    def get_duration(self, dep_time, nodes, day):
        current_time = dep_time
        if(len(nodes)==1):
            return (current_time, dep_time)
        else:
            times = [(current_time, 0, dep_time)]
            for i in range(0, len(nodes) - 1):
                dep = self.graph.get_start(nodes[i], nodes[i+1], current_time, day)
                arr = self.graph.get_arrival(nodes[i], nodes[i+1], current_time, day)
                waiting = dep-current_time
                times.append((dep,waiting,arr))
                current_time = arr
            return (times[1][0], times[-1][2])


 
