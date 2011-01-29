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
#    © Université Toulouse 1 Capitole 2010
#    © Tristram Gräbener 2011
#    Author: Tristram Gräbener, Odysseas Gabrielides

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
    def __init__(self, id, lon, lat, route, stop_area, the_geom = ""):
        self.original_id = id
        self.lon = lon
        self.lat = lat
        self.route = route
        self.the_geom = the_geom
        self.stop_area = stop_area

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
    def __init__(self, source, target, length, start_secs, arrival_secs, services, mode, line):
        self.source = source
        self.target = target
        self.length = length
        self.start_secs = start_secs
        self.arrival_secs = arrival_secs
        self.services = services
        self.mode = mode
        self.line = line

class PT_Line(object):
    def __init__(self, code, short_name, long_name, color, text_color, desc):
        self.code = code
        self.short_name = short_name
        self.long_name = long_name
        self.color = color
        self.text_color = text_color
        self.desc = desc

class PT_StopArea(object):
    def __init__(self, code, name):
        self.code = code
        self.name = name

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

def create_pt_nodes_table(id, metadata, stop_areas_table):
    table = Table(id, metadata, 
            Column('id', Integer, primary_key = True),
            Column('original_id', String, index = True),
            Column('lon', Float, index = True),
            Column('lat', Float),
            Column('the_geom', String),
            Column('route', String),
            Column('stop_area', Integer, ForeignKey(stop_areas_table + ".id"))
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
            
def create_pt_edges_table(id, metadata, services_table, lines_table):
    table = Table(id, metadata,
            Column('id', Integer, primary_key = True),
            Column('source', Integer, index = True),
            Column('target', Integer, index = True),
            Column('length', Float),
            Column('start_secs', Integer),
            Column('arrival_secs', Integer),
            Column('services', Integer,  ForeignKey(services_table + ".id")),
            Column('mode', Integer),
            Column('line', Integer, ForeignKey(lines_table + ".id"))
            )
    metadata.create_all()
    return table

def create_pt_lines_table(id, metadata):
    table = Table(id, metadata,
            Column('id', Integer, primary_key = True),
            Column('code', String),
            Column('short_name', String),
            Column('long_name', String),
            Column('color', String),
            Column('text_color', String),
            Column('desc', String)
            )
    metadata.create_all()
    return table

def create_pt_stop_areas_table(id, metadata):
    table = Table(id, metadata,
            Column('id', Integer, primary_key = True),
            Column('code', String, index = True),
            Column('name', String)
            )
    metadata.create_all()
    return table
