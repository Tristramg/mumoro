#!/usr/bin/env python
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

from lib.core import mumoro
from lib.core.mumoro import Bike, Car, Foot, PublicTransport, cost, co2, dist, elevation, line_change, mode_change, penibility, Costs
from lib import layer

from lib import bikestations as bikestations
from lib import utils
from web import shorturl

from sqlalchemy import *
from sqlalchemy.orm import mapper, sessionmaker, clear_mappers

import cherrypy
import sys
import simplejson as json
import os
import time
import urllib
import httplib
import hashlib
import datetime

from cherrypy import request
from genshi.template import TemplateLoader

layer_array = []
bike_stations_array = []
same_nodes_connection_array = []
nearest_nodes_connection_array = []
nodes_list_connection_array = []
paths_array = []
            

# Loads an osm (compressed of not) file and insert data into database
def import_street_data( filename ):
    engine = create_engine( db_type + ":///" + db_params )
    metadata = MetaData(bind = engine)
    mumoro_metadata = Table('metadata', metadata, autoload = True)
    s = mumoro_metadata.select((mumoro_metadata.c.origin == filename) & (mumoro_metadata.c.node_or_edge == 'Nodes'))
    rs = s.execute().first()
    nd = rs[0] if rs else 0
    s = mumoro_metadata.select((mumoro_metadata.c.origin == filename) & (mumoro_metadata.c.node_or_edge == 'Edges'))
    rs = s.execute().first()
    ed = rs[0] if rs else 0
    return {'nodes': str(nd), 'edges' : str(ed)}
    

# Loads the tables corresponding to the public transport layer
def import_gtfs_data( filename, network_name = "Public Transport"):
    engine = create_engine(db_type + ":///" + db_params)
    metadata = MetaData(bind = engine)
    mumoro_metadata = Table('metadata', metadata, autoload = True)
    nd = mumoro_metadata.select((mumoro_metadata.c.origin == filename) & (mumoro_metadata.c.node_or_edge == 'Nodes')).execute().first()[0]
    ed = mumoro_metadata.select((mumoro_metadata.c.origin == filename) & (mumoro_metadata.c.node_or_edge == 'Edges')).execute().first()[0]
    services = mumoro_metadata.select((mumoro_metadata.c.origin == filename) & (mumoro_metadata.c.node_or_edge == 'Services')).execute().first()[0]
    lines = mumoro_metadata.select((mumoro_metadata.c.origin == filename) & (mumoro_metadata.c.node_or_edge == 'Lines')).execute().first()[0]
    stop_areas = mumoro_metadata.select((mumoro_metadata.c.origin == filename) & (mumoro_metadata.c.node_or_edge == 'StopAreas')).execute().first()[0]
    
    return {'nodes': str(nd), 'edges' : str(ed), 'services': str(services),
            'lines': str(lines), 'stop_areas': str(stop_areas)}

def import_kalkati_data(filename, network_name = "Public Transport"):
    return import_gtfs_data(filename, network_name)


def import_freq_data(line_name, nodesf, linesf, start_date, end_date):
     return import_gtfs_data(line_name)


# Loads a bike service API ( from already formatted URL ). Insert bike stations in database and enables schedulded re-check.
def import_bike_service( url, name ):
    engine = create_engine(db_type + ":///" + db_params)
    metadata = MetaData(bind = engine)
    mumoro_metadata = Table('metadata', metadata, autoload = True)
    s = mumoro_metadata.select((mumoro_metadata.c.origin == url) & (mumoro_metadata.c.node_or_edge == 'bike_stations'))
    rs = s.execute().first()
    bt = rs[0] if rs else 0
    bike_stations_array.append( {'url_api': url,'table': str(bt)} )
    return {'url_api': url,'table': str(bt)}


# Loads data from previous inserted data and creates a layer used in multi-modal graph
def street_layer( data, name, color, mode, bike_service=None ):
    if not data or not name:
        raise NameError('One or more parameters are missing')
    if not utils.valid_color_p( color ):
        raise NameError('Color for the layer is invalid')
    if mode != mumoro.Foot and mode != mumoro.Bike and mode != mumoro.Car and mode != None:
        raise NameError('Wrong layer mode paramater')
    engine = create_engine(db_type + ":///" + db_params)
    metadata = MetaData(bind = engine)
    res = layer.Layer(name, mode, data, metadata, bike_service)
    layer_array.append( {'layer':res,'name':name,'mode':mode,'origin':data,'color':color} )
    return {'layer':res,'name':name,'mode':mode,'origin':data,'color':color} 

def public_transport_layer(data, name, color): 
    engine = create_engine(db_type + ":///" + db_params)
    metadata = MetaData(bind = engine)
    res = layer.GTFSLayer(name, data, metadata)
    layer_array.append( {'layer':res,'name':name,'mode':PublicTransport,'origin':data,'color':color} )
    return {'layer':res,'name':name,'mode':PublicTransport,'origin':PublicTransport,'color':color} 

# vérifie le type des objectifs et ajoute à la variable globale paths_array les couches et les objectifs
def paths( starting_layer, destination_layer, objectives, epsilon = None ):
    if not starting_layer or not destination_layer:
        raise NameError('Empty layer(s)')
    def valid_obj(o): return [mumoro.dist, mumoro.cost, mumoro.elevation,
                              mumoro.co2, mumoro.mode_change, mumoro.line_change, mumoro.penibility].index(o)
    c = map(valid_obj,objectives)
    paths_array.append( {'starting_layer':starting_layer,'destination_layer':destination_layer,'objectives':objectives, 'epsilon': epsilon} )

        
# Creates a transit cost variable, including the duration in seconds of the transit and if the mode is changed
def cost( duration, mode_change ):
    e = mumoro.Edge()
    e.mode_change = 1 if mode_change else 0
    e.duration = mumoro.Duration( duration );
    return e

# Connects 2 given layers on same nodes with the given cost(s)
def connect_layers_same_nodes( layer1, layer2, cost ):
    if not layer1 or not layer2 or not cost:
        raise NameError('One or more paramaters are empty')
    same_nodes_connection_array.append( { 'layer1':layer1, 'layer2':layer2, 'cost':cost } )

# Connect 2 given layers on a node list (arg 3 which
# should be the returned data from import_municipal_data
# or import_bike_service) with the given cost(s)
def connect_layers_from_node_list( layer1, layer2, node_list, cost, cost2 = None ):
    if not layer1 or not layer2 or not node_list or not cost:
        raise NameError('One or more paramaters are empty')
    if not cost2:
        nodes_list_connection_array.append( { 'layer1':layer1, 'layer2':layer2, 'node_list':node_list, 'cost1':cost, 'cost2':cost } )
    else:
        nodes_list_connection_array.append( { 'layer1':layer1, 'layer2':layer2, 'node_list':node_list, 'cost1':cost, 'cost2':cost2 } )

# Connect 2 given layers on nearest nodes
def connect_layers_on_nearest_nodes( layer1 , layer2, cost, cost2 = None):
    if not layer1 or not layer2 or not cost:
        raise NameError('One or more paramaters are empty')
    nearest_nodes_connection_array.append( { 'layer1':layer1, 'layer2':layer2, 'cost':cost, 'cost2':cost2 } )


class Mumoro(object):
    def __init__(self,db_string,config_file,):
        self.loader = TemplateLoader(os.path.join(os.path.dirname(__file__), 
                                                  'web/templates'),
                                     auto_reload=True)
        if not layer_array:
            raise NameError('Can not create multimodal graph beceause there are no layers')
        layers = []
        for i in layer_array:
            layers.append( i['layer'] )
        for i in range( len( layer_array ) ):
            for j in range( len( layer_array ) ):
                if i != j:
                    if layer_array[i]['name'] == layer_array[j]['name']:
                        raise NameError('Layers can not have the same name')
        if len( paths_array ) == 0:
            print 'Warning: there are no defined paths !'
        self.engine = create_engine(db_string)
        self.metadata = MetaData(bind = self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.bike_stations = []
        for i in bike_stations_array:
            self.bike_stations.append( bikestations.BikeStationImporter(i['url_api'],i['table'],self.metadata) )
        for i in self.bike_stations:
            i.update_from_db()
        self.timestamp = time.time()
        self.config_table = Table('config', self.metadata,
            Column('config_file', String, primary_key = True),
            Column('binary_file', String, primary_key = True),
            Column('md5', String, index = True)
            )
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
        Column('chrone', DateTime(timezone=False))
        )
        self.metadata.create_all()
        s = self.config_table.select()
        rs = s.execute()
        row = rs.fetchone()
        if row and row['md5']== utils.md5_of_file( file( config_file ) ) and os.path.exists( os.getcwd() + "/" + row['binary_file'] ):
                print "No need to rebuilt graph : configuration didn't change so loading from binary file"
                self.g = layer.MultimodalGraph(layers, str(row['binary_file']))
        else:
            if not row:
                print "This is the first time of launch: creating multimodal graph from scratch"
            elif row['md5'] != utils.md5_of_file( file( config_file ) ):
                print "Configuration has changed since last launch. Rebuilding multimodal graph"
                if os.path.exists( os.getcwd() + "/" + row['binary_file'] ) :
                    os.remove(os.getcwd() + "/" + row['binary_file'])   
                self.config_table.delete().execute()
                self.session.commit()
            elif not os.path.exists( os.getcwd() + "/" + row['binary_file'] ) :
                print "Configuration has not changed since last launch but binary file is missing. Rebuilding multimodal graph"
                self.config_table.delete().execute()
                self.session.commit()
            self.g = layer.MultimodalGraph( layers )
            for i in same_nodes_connection_array:
                self.g.connect_same_nodes( i['layer1']['layer'],i['layer2']['layer'],i['cost'] )
            for i in nearest_nodes_connection_array:
                self.g.connect_nearest_nodes( i['layer1']['layer'],i['layer2']['layer'],i['cost'], i['cost2'] )
            for i in nodes_list_connection_array:
               try:
                   i['node_list']['url_api']
                   print 'Assuming that the nodes list are bike stations'
                   for j in self.bike_stations:
                       if j.url == i['node_list']['url_api']:
                            self.g.connect_nodes_from_list( i['layer1']['layer'],i['layer2']['layer'],j.stations,i['cost1'],i['cost2'] )
                            break
               except KeyError:
                   try:
                       i['node_list']['layer']
                       print 'Assuming that the nodes list is a public transport layer'
                       self.g.connect_nodes_from_list( i['layer1']['layer'],i['layer2']['layer'],i['node_list']['layer'].nodes(),i['cost1'],i['cost2'] )
                   except KeyError:
                       raise NameError('Can not connect layers from the node list')
            md5_config_checksum = utils.md5_of_file( file( config_file ) )
            self.g.save( md5_config_checksum + '.dump' )
            i = self.config_table.insert()
            i.execute({'config_file': config_file, 'md5': md5_config_checksum, 'binary_file': md5_config_checksum + '.dump'})








    @cherrypy.expose
    def path(self, slon, slat, dlon, dlat, time):
        u_obj = []
        #Creates the union of all used objectives
        for p in paths_array:
            for o in p['objectives'] :
                if not o in u_obj:
                    u_obj.append( o )
        u_obj = self.sort_objectives( u_obj )
        p = tuple()
        c = self.analyse_date( time )
        #Call martins with the sorted objectives
        for y in paths_array:
            s = self.g.match( y['starting_layer']['name'], float(slon), float(slat))
            d = self.g.match( y['destination_layer']['name'], float(dlon), float(dlat))
            obj = y['objectives']
            eps = y['epsilon']
            nb_obj = len( obj )
            print c['seconds'], c['days']
            if eps == None:
                if nb_obj == 0:
                    p = p + self.normalise_paths( mumoro.martins(s, d, self.g.graph,c['seconds'], c['days']),[],u_obj )
                elif nb_obj == 1:
                    p = p + self.normalise_paths( mumoro.martins(s, d, self.g.graph,c['seconds'], c['days'], obj[0] ), [ obj[0] ], u_obj )
                elif nb_obj == 2:
                    p = p + self.normalise_paths( mumoro.martins(s, d, self.g.graph,c['seconds'], c['days'], obj[0], obj[1] ), [ obj[0], obj[1] ], u_obj )
                elif nb_obj >= 3:
                    p = p + self.normalise_paths( mumoro.martins(s, d, self.g.graph,c['seconds'], c['days'], obj[0], obj[1], obj[2] ), [ obj[0], obj[1], obj[2] ], u_obj )
            else:
                if nb_obj == 0:
                    p = p + mumoro.martins(s, d, self.g.graph,c['seconds'], c['days'])
                elif nb_obj == 1:
                    p = p + self.normalise_paths(mumoro.relaxed_martins(s, d, self.g.graph,c['seconds'], c['days'], obj[0], eps[0]) , [ obj[0] ], u_obj )
                elif nb_obj == 2:
                    p = p + self.normalise_paths(mumoro.relaxed_martins(s, d, self.g.graph,c['seconds'], c['days'], obj[0], eps[0], obj[1], eps[1] ), [ obj[0], obj[1] ], u_obj ) 
                elif nb_obj >= 3:
                    p = p + self.normalise_paths(mumoro.relaxed_martins(s, d, self.g.graph,c['seconds'], c['days'], obj[0], eps[0], obj[1], eps[1], obj[2], eps[2] ), [ obj[0], obj[1], obj[2] ], u_obj )
            print "Longueur de p : ", len(p)
        #Creates the array containing the user-oriented string for each objective
        str_obj = ['Duration']
        for j in u_obj:
            if j == mumoro.dist:
                str_obj.append( 'Distance' )
            elif j == mumoro.cost:
                str_obj.append( 'Cost' )
            elif j == mumoro.elevation:
                str_obj.append( 'Elevation ' )
            elif j == mumoro.co2:
                str_obj.append( 'CO2 Emission' )
            elif j == mumoro.mode_change:
                str_obj.append( 'Mode Change' )
            elif j == mumoro.line_change:
                str_obj.append( 'Line Change' )
            elif j == mumoro.penibility:
                str_obj.append( 'Penibility' )
        cherrypy.response.headers['Content-Type']= 'application/json'
        if len(p) == 0:
            return json.dumps({'error': 'Impossible de calculer un itinéraire'})
        print "Len of routes " + str( len( p ) )
        print "len of first route " + str (len (p[0].nodes))
#        print "route " + p[0].nodes[0]
        ret = {
                'objectives': str_obj,
                'paths': []
                }
        def layer_split(l,x):
            if(len(l[-1]) == 0):
                l[-1].append(x)
            elif(l[-1][-1][1] == x[1]):
                if (l[-1][-1][1].mode == mumoro.PublicTransport and
                    l[-1][-1][0].route != x[0].route):
                    l.append([x])
                else:
                    l[-1].append(x)
            else:
                l.append([x])
            return l
                        
        for path in p:
            p_str = {
                    'cost': [],
                    'type': 'FeatureCollection',
                    'crs': {
                        'type': 'EPSG',
                        'properties': {
                            'code': 4326,
                            'coordinate_order': [1,0]
                            }
                        }
                    }
            for c in path.cost:
                p_str['cost'].append(c)

            it = reduce(layer_split, 
                        [[self.g.layer_object(node_id).node(node_id), 
                          self.g.layer_object(node_id), 
                          node_id] for node_id in path.nodes],
                        [[]])
            features = [{'type': 'feature',
                         'geometry':  {'type': 'Linestring',
                                       'coordinates': [[node[0].lon, node[0].lat] for node in seq]},
                         'properties': {'layer': seq[0][1].layer_name(),
                                        'icon': seq[0][1].icon(seq[0][0]),
                                        'color': seq[0][1].color(seq[0][0])}}
                        for seq in it]
            features.extend([ {"type":"Feature",
                               "geometry":{"type":"Point",
                                           "coordinates": [seq[0][0].lon,
                                                           seq[0][0].lat]},
                               "properties": { "line": seq[0][0].route,
                                               "layer": "marker",
                                               "headsign": seq[0][0].headsign,
                                               "marker_icon": 
                                               seq[0][1].marker_icon(seq[0][0]),
                                               "line_icon": 
                                               seq[0][1].icon(seq[0][0]),
                                               "line_name":
                                                   seq[0][1].line(seq[0][0]).long_name,
                                               "stop_area": 
                                               seq[0][1].
                                               stop_area(seq[0][0].original_id).name,
                                               "dest_stop_area": seq[-1][1].stop_area(seq[-1][0].original_id).name,
                                               "type": "bus_departure"}} for seq in it if seq[0][1].mode == mumoro.PublicTransport])
            features.extend([{"type":"Feature",
                              "geometry":{"type":"Point",
                                          "coordinates": [seq[0][0].lon,
                                                          seq[0][0].lat]},
                              "properties": { "layer": "marker",
                                              "marker_icon": seq[0][1].marker_icon(seq[0][0]),
                                              "bikes_av": seq[0][1].bike_station(seq[0][0]).av_bikes,
                                              "slots_av": seq[0][1].bike_station(seq[0][0]).av_slots,
                                              "station_name": seq[0][1].bike_station(seq[0][0]).name,
                                              "dest_station_name": seq[-1][1].bike_station(seq[-1][0]).name,
                                              "type": "bike_departure"}} for seq in it if seq[0][1].mode == mumoro.Bike])
            p_str['features'] = features
            ret['paths'].append(p_str)
        return json.dumps(ret)
    
    @cherrypy.expose
    def bikes(self):
        if len( self.bike_stations ) > 0:
            if time.time() > self.timestamp + 60 * 5:
                print "Updating bikestations"
                for i in self.bike_stations:
                    i.import_data()
                print "Done !"
            for i in self.bike_stations:
                i.update_from_db()
            res = 'lat\tlon\ttitle\tdescription\ticon\ticonSize\ticonOffset\n'
            for i in self.bike_stations:
                res += i.to_string()
            print "Got string"
            return res;
        else:
            print "No bike stations imported so no string available to generate"
            return None

    @cherrypy.expose
    def addhash(self,mlon,mlat,zoom,slon,slat,dlon,dlat,saddress,daddress,time):
        cherrypy.response.headers['Content-Type']= 'application/json'
        hashAdd = shorturl.shortURL(self.metadata)
        hmd5 =hashAdd.addRouteToDatabase(mlon,mlat,zoom,slon,slat,dlon,dlat,saddress,daddress, time)
        if( len(hmd5) > 0 ):
            return json.dumps({ 'h': hmd5 })
        else:
            return '{"error": "Add to DB failed"}'

    @cherrypy.expose
    def h(self,id):
        hashCheck = shorturl.shortURL(self.metadata)
        res = hashCheck.getDataFromHash(id)
        if( len(res) > 0 ):
            return self.index(True,res)
        else:
            return self.index(False,res)

    @cherrypy.expose
    def index(self,fromHash=False,hashData=[]):
        tmpl = self.loader.load('index.html')
        t = "{"
        for i in range( len( layer_array ) ):
            t = t + "\"" + layer_array[i]['name'] + "\": { strokeColor : \"" + layer_array[i]['color'] + "\"}"
            if i != len( layer_array ) - 1 :
                t = t + ","
        t = t + "}"
        if( not fromHash ):
            return tmpl.generate(fromHash='false',
                                 lonStart=-1.688976,latStart=48.122070,
                                 lonDest=-1.659279,latDest=48.103045,
                                 addressStart='',addressDest='',
                                 hashUrl=request.config['mumoro.web_url'],
                                 layers=t, 
                                 date=datetime.datetime.today().
                                 strftime("%d/%m/%Y %H:%M"),
                                 googleanalytics=request.config['mumoro.googleanalytics'],
                                 cloudmadeapi=request.config['mumoro.cloudmadeapi']).render('html', doctype='html5')
        else:
            return tmpl.generate(fromHash='true',
                                 lonStart=hashData[4],
                                 latStart=hashData[5],
                                 lonDest=hashData[6],
                                 latDest=hashData[7],
                                 addressStart=hashData[8].decode('utf-8'),
                                 addressDest=hashData[9].decode('utf-8'),
                                 hashUrl=request.config['mumoro.web_url'],
                                 layers=t,date=hashData[10],
                                 googleanalytics=request.config['mumoro.googleanalytics'],
                                 cloudmadeapi=request.config['mumoro.cloudmadeapi']).render('html', doctype='html5')

    @cherrypy.expose
    def info(self):
        tmpl = self.loader.load('info.html')
        return tmpl.generate().render('html', doctype='html5')
    
    @cherrypy.expose
    def geo(self,q):
        cherrypy.response.headers['Content-Type']= 'application/json'
        url = "nominatim.openstreetmap.org:80"
        params = urllib.urlencode({
          "q": q.encode("utf-8"),
          "format":"json",
          "polygon": 0,
          "addressdetails" : 1,
          "limit": 1,
          "email" : request.config['mumoro.admin_email']
        })
        conn = httplib.HTTPConnection(url)
        conn.request("GET", "/search?" + params)
        response = conn.getresponse()
        ret = json.loads(response.read())
        is_covered = False
        if ret:
                cord_error = ""
                lon = ret[0]['lon']
                lat = ret[0]['lat']
                display_name = ret[0]['display_name']
                if self.arecovered(lon,lat):
                        node_error = ""
                        is_covered = True
                else:
                        node_error = "not covered area"
        else:
                cord_error = "geocoding failed"
                lon = 0
                lat = 0
                display_name = ""
                node_error = "match failed because geocoding failed"
        data = {
                'lon': lon,
                'lat': lat,
                'display_name': display_name,
                'node_error': node_error,
                'cord_error': cord_error,
                'is_covered': is_covered
        }
        return json.dumps(data)

    @cherrypy.expose
    def revgeo(self,lon,lat):
        cherrypy.response.headers['Content-Type']= 'application/json'
        url = "nominatim.openstreetmap.org:80"
        params = urllib.urlencode({
          "lon": lon,
          "lat": lat,
          "format":"json",
          "zoom": 18,
          "addressdetails" : 1,
          "email" : request.config['mumoro.admin_email']
        })
        conn = httplib.HTTPConnection(url)
        conn.request("GET", "/reverse?" + params)
        response = conn.getresponse()
        ret = json.loads(response.read())
        is_covered = False
        if ret:
                cord_error = ""
                display_name = ret['display_name']
                if self.arecovered(float(lon),float(lat)):
                        node_error = ""
                        is_covered = True
                else:
                        node_error = "not covered area"
        else:
                cord_error = "geocoding failed"
                display_name = ""
                node_error = "match failed because revgeocoding failed"
        data = {
                'display_name': display_name,
                'node_error': node_error,
                'cord_error': cord_error,
                'is_covered': is_covered
        }
        return json.dumps(data)

    def arecovered(self,lon,lat):
        return True
        for i in layer_array:
            b = i['layer'].borders()
            if lon >= b['min_lon'] and lon <= b['max_lon'] and lat >= b['min_lat'] and lat <= b['max_lat']:
                return True
            else:
                print lon,lat, b
        return False

    def sort_objectives(self,obj):
        res = []
        #Sorts the objective array in a unique way
        if mumoro.cost in obj:
            res.append( mumoro.cost )
        if mumoro.co2 in obj:
            res.append( mumoro.co2 )
        if mumoro.dist in obj:
            res.append( mumoro.dist )
        if mumoro.elevation in obj and len( res ) < 3:
            res.append( mumoro.elevation )
        if mumoro.line_change in obj and len( res ) < 3:
            res.append( mumoro.line_change )  
        if mumoro.mode_change in obj and len( res ) < 3:
            res.append( mumoro.mode_change )
        if mumoro.penibility in obj :
            res.append( mumoro.penibility )
        return res

    def normalise_paths(self,route,used_objectives,union_objectives):
        for i in route:
            if len( union_objectives ) + 1 != len( i.cost ):
                tmp = Costs()
                tmp.append( i.cost[0] )
                for j in range( len( union_objectives ) ):
                    if j < len( used_objectives ):
                        if used_objectives[j] == union_objectives[j]:
                            tmp.append( i.cost[j + 1] )
                        else:
                            tmp.append( 0.0 )
                    else:
                         tmp.append( 0.0 )
                i.cost = tmp
        return route

    def analyse_date(self,date):
        now_chrone = datetime.datetime.strptime(date, "%d/%m/%Y %H:%M")
        start_chrone = datetime.datetime.strptime(start_date, "%Y%m%d")
        past_seconds = now_chrone.hour * 60 * 60 + now_chrone.minute * 60 + now_chrone.second
        delta = now_chrone - start_chrone
        return {'seconds':past_seconds,'days':delta.days} 
        

def mumoro_namespace(k, v):
    pass

cherrypy.config.namespaces['mumoro'] = mumoro_namespace

cherrypy.config.update(os.path.abspath(os.path.dirname(__file__)) + '/cherrypy.config')

if cherrypy.config["mumoro.scenario"] == None or not os.path.exists(cherrypy.config["mumoro.scenario"]):
    raise NameError('Scenario configuration file does not exist "%s"' % cherrypy.config["mumoro.scenario"])
exec(file(cherrypy.config["mumoro.scenario"]))

cherrypy.config.update({
    'tools.encode.on': True,
    'tools.encode.encoding': 'utf-8',
    'tools.decode.on': True,
    'tools.trailing_slash.on': True,
    'tools.staticdir.root': os.path.abspath(os.path.dirname(__file__)) + "/web/",
})

cherrypy.quickstart(Mumoro(db_type + ":///" + db_params, 
                           cherrypy.config["mumoro.scenario"]), 
                    '/',
                    config={'/static': {'tools.staticdir.on': True,
                                        'tools.staticdir.dir': 'static'}
                            }
                    )
