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


from lib.core import mumoro
from lib.core.mumoro import Bike, Car, Foot, PublicTransport, cost, co2, dist, elevation, line_change, mode_change, Costs
from lib import layer

from lib import bikestations as bikestations
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

loader = TemplateLoader(
    os.path.join(os.path.dirname(__file__), 'web/templates'),
    auto_reload=True
)

layer_array = []
bike_stations_array = []
same_nodes_connection_array = []
nearest_nodes_connection_array = []
nodes_list_connection_array = []

paths_array = []

def md5_of_file(filename):
    block_size=2**20
    md5 = hashlib.md5()
    while True:
        data = filename.read(block_size)
        if not data:
            break
        md5.update(data)
    filename.close()
    return md5.hexdigest()

def is_color_valid( color ):
    if len( color ) == 7:
        if color[0] == '#':
            try:
                r = int( color[1:3], 16)
                if r <= 255 and r >= 0:
                    try:
                        g = int( color[3:5], 16)
                        if g <= 255 and g >= 0:
                            try:
                                b = int( color[5:7], 16)
                                if b <= 255 and b >= 0:
                                    return True
                            except ValueError:
                                return False
                    except ValueError:
                        return False
            except ValueError:
                return False
    return False

#Loads an osm (compressed of not) file and insert data into database
def import_street_data( filename ):
    engine = create_engine( db_type + ":///" + db_params )
    metadata = MetaData(bind = engine)
    mumoro_metadata = Table('metadata', metadata, autoload = True)
    s = mumoro_metadata.select((mumoro_metadata.c.origin == filename) & (mumoro_metadata.c.node_or_edge == 'Nodes'))
    rs = s.execute()
    nd = 0
    for row in rs:
         nd = row[0]
    s = mumoro_metadata.select((mumoro_metadata.c.origin == filename) & (mumoro_metadata.c.node_or_edge == 'Edges'))
    rs = s.execute()
    ed = 0
    for row in rs:
         ed = row[0]
    return {'nodes': str(nd), 'edges' : str(ed)}


# Loads the tables corresponding to the public transport layer
def import_gtfs_data( filename, network_name = "Public Transport"):
    engine = create_engine(db_type + ":///" + db_params)
    metadata = MetaData(bind = engine)
    mumoro_metadata = Table('metadata', metadata, autoload = True)
    nd = mumoro_metadata.select((mumoro_metadata.c.origin == filename) & (mumoro_metadata.c.node_or_edge == 'Nodes')).execute().first()[0]

    ed = mumoro_metadata.select((mumoro_metadata.c.origin == filename) & (mumoro_metadata.c.node_or_edge == 'Edges')).execute().first()[0]
    
    services = mumoro_metadata.select((mumoro_metadata.c.origin == filename) & (mumoro_metadata.c.node_or_edge == 'Services')).execute().first()[0]

    return {'nodes': str(nd), 'edges' : str(ed), 'services': str(services) }

def import_kalkati_data(filename, network_name = "Public Transport"):
    return import_gtfs_data(filename, network_name)

#Loads a bike service API ( from already formatted URL ). Insert bike stations in database and enables schedulded re-check.
def import_bike_service( url, name ):
    engine = create_engine(db_type + ":///" + db_params)
    metadata = MetaData(bind = engine)
    mumoro_metadata = Table('metadata', metadata, autoload = True)
    s = mumoro_metadata.select((mumoro_metadata.c.origin == url) & (mumoro_metadata.c.node_or_edge == 'bike_stations'))
    rs = s.execute()
    for row in rs:
         bt = row[0]
    bike_stations_array.append( {'url_api': url,'table': str(bt)} )
    return {'url_api': url,'table': str(bt)}

#Loads data from previous inserted data and creates a layer used in multi-modal graph
def street_layer( data, name, color, mode ):
    if not data or not name:
        raise NameError('One or more parameters are missing')
    if not is_color_valid( color ):
        raise NameError('Color for the layer is invalid')
    if mode != mumoro.Foot and mode != mumoro.Bike and mode != mumoro.Car and mode != None:
        raise NameError('Wrong layer mode paramater')
    engine = create_engine(db_type + ":///" + db_params)
    metadata = MetaData(bind = engine)
    res = layer.Layer(name, mode, data, metadata)
    layer_array.append( {'layer':res,'name':name,'mode':mode,'origin':data,'color':color} )
    return {'layer':res,'name':name,'mode':mode,'origin':data,'color':color} 
    
def public_transport_layer(data, name, color): 
    engine = create_engine(db_type + ":///" + db_params)
    metadata = MetaData(bind = engine)
    res = layer.GTFSLayer(name, data, metadata)
    layer_array.append( {'layer':res,'name':name,'mode':PublicTransport,'origin':data,'color':color} )
    return {'layer':res,'name':name,'mode':PublicTransport,'origin':PublicTransport,'color':color} 

def paths( starting_layer, destination_layer, objectives ):
    if not starting_layer or not destination_layer:
        raise NameError('Empty layer(s)')
    for i in range( len( objectives ) ):
        if objectives[i] != mumoro.dist and objectives[i] != mumoro.cost and objectives[i] != mumoro.elevation and objectives[i] != mumoro.co2 and objectives[i] != mumoro.mode_change and objectives[i] != mumoro.line_change:
            raise NameError('Wrong objective parameter')
    paths_array.append( {'starting_layer':starting_layer,'destination_layer':destination_layer,'objectives':objectives} )

#Creates a transit cost variable, including the duration in seconds of the transit and if the mode is changed
def cost( duration, mode_change ):
    e = mumoro.Edge()
    if mode_change:
        e.mode_change = 1
    else:
        e.mode_change = 0
    e.duration = mumoro.Duration( duration );
    return e

#Connects 2 given layers on same nodes with the given cost(s)
def connect_layers_same_nodes( layer1, layer2, cost ):
    if not layer1 or not layer2 or not cost:
        raise NameError('One or more paramaters are empty')
    same_nodes_connection_array.append( { 'layer1':layer1, 'layer2':layer2, 'cost':cost } )

#Connect 2 given layers on a node list (arg 3 which should be the returned data from import_municipal_data or import_bike_service) with the given cost(s)
def connect_layers_from_node_list( layer1, layer2, node_list, cost, cost2 = None ):
    if not layer1 or not layer2 or not node_list or not cost:
        raise NameError('One or more paramaters are empty')
    if not cost2:
        nodes_list_connection_array.append( { 'layer1':layer1, 'layer2':layer2, 'node_list':node_list, 'cost1':cost, 'cost2':cost } )
    else:
        nodes_list_connection_array.append( { 'layer1':layer1, 'layer2':layer2, 'node_list':node_list, 'cost1':cost, 'cost2':cost2 } )

#Connect 2 given layers on nearest nodes
def connect_layers_on_nearest_nodes( layer1 , layer2, cost, cost2 = None):
    if not layer1 or not layer2 or not cost:
        raise NameError('One or more paramaters are empty')
    nearest_nodes_connection_array.append( { 'layer1':layer1, 'layer2':layer2, 'cost':cost, 'cost2':cost2 } )

class Mumoro:
    def __init__(self,db_string,config_file,admin_email,web_url):
        if not admin_email:
            raise NameError('Administrator email is empty')
        self.admin_email = admin_email
        if not web_url:
            raise NameError('Website URL is empty')
        self.web_url = web_url
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
        if row and row['md5']== md5_of_file( file( config_file ) ) and os.path.exists( os.getcwd() + "/" + row['binary_file'] ):
                print "No need to rebuilt graph : configuration didn't change so loading from binary file"
                self.g = layer.MultimodalGraph(layers, str(row['binary_file']))
        else:
            if not row:
                print "This is the first time of launch: creating multimodal graph from scratch"
            elif row['md5'] != md5_of_file( file( config_file ) ):
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
            md5_config_checksum = md5_of_file( file( config_file ) )
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
            tmp = y['objectives']
            tmp = self.sort_objectives( tmp )
            t = len( tmp )
            print c['seconds'], c['days']
            if t == 0:
                p = p + self.normalise_paths( mumoro.martins(s, d, self.g.graph,c['seconds'], c['days']),[],u_obj )
            elif t == 1:
                p = p + self.normalise_paths( mumoro.martins(s, d, self.g.graph,c['seconds'], c['days'], tmp[0] ), [ tmp[0] ], u_obj )
            elif t == 2:
                p = p + self.normalise_paths( mumoro.martins(s, d, self.g.graph,c['seconds'], c['days'], tmp[0], tmp[1] ), [ tmp[0], tmp[1] ], u_obj )
            elif t >= 3:
                p = p + self.normalise_paths( mumoro.martins(s, d, self.g.graph,c['seconds'], c['days'], tmp[0], tmp[1], tmp[2] ), [ tmp[0], tmp[1], tmp[2] ], u_obj )
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
        cherrypy.response.headers['Content-Type']= 'application/json'
        if len(p) == 0:
            return json.dumps({'error': 'No route found'})
        print "Len of routes " + str( len( p ) )
        ret = {
                'objectives': str_obj,
                'paths': []
                }
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

            features = []
            feature = {'type': 'feature'}
            geometry = {'type': 'Linestring'}
            coordinates = []
            last_node = path.nodes[0]
            last_coord = self.g.coordinates(last_node)
            for node in path.nodes:
                coord = self.g.coordinates(node)
                if(last_coord[3] != coord[3]):
                    geometry['coordinates'] = coordinates
                    feature['geometry'] = geometry
                    feature['properties'] = {'layer': last_coord[3]}
                    features.append(feature)

                    feature = {'type': 'feature'}
                    geometry = {'type': 'Linestring'}
                    coordinates = []

                    connection = {
                            'type': 'feature',
                            'geometry': {
                                'type': 'Linestring',
                                'coordinates': [[last_coord[0], last_coord[1]], [coord[0], coord[1]]]
                                },
                            'properties': {'layer': 'connection'}
                            }
                    features.append(connection);
                last_node = node
                last_coord = coord
                coordinates.append([coord[0], coord[1]])
            geometry['coordinates'] = coordinates
            feature['geometry'] = geometry
            feature['properties'] = {'layer': last_coord[3]}
            features.append(feature)
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
            ret = {
                'h': hmd5
            }
            return json.dumps(ret)
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
        tmpl = loader.load('index.html')
        t = "{"
        for i in range( len( layer_array ) ):
            t = t + "\"" + layer_array[i]['name'] + "\": { strokeColor : \"" + layer_array[i]['color'] + "\"}"
            if i != len( layer_array ) - 1 :
                t = t + ","
        t = t + "}"
        if( not fromHash ):
            a = paths_array[0]['starting_layer']['layer'].average()
            b = paths_array[0]['starting_layer']['layer'].borders()
            return tmpl.generate(fromHash='false',lonMap=a['avg_lon'],latMap=a['avg_lat'],zoom=14,lonStart=b['min_lon'],latStart=b['min_lat'],lonDest=b['max_lon'],latDest=b['max_lat'],addressStart='',addressDest='',hashUrl=self.web_url,layers=t, date=datetime.datetime.today().strftime("%d/%m/%Y %H:%M")).render('html', doctype='html')
        else:
            return tmpl.generate(fromHash='true',lonMap=hashData[2],latMap=hashData[3],zoom=hashData[1],lonStart=hashData[4],latStart=hashData[5],lonDest=hashData[6],latDest=hashData[7],addressStart=hashData[8].decode('utf-8'),addressDest=hashData[9].decode('utf-8'),hashUrl=self.web_url,layers=t,date=hashData[10]).render('html', doctype='html')

    @cherrypy.expose
    def info(self):
        tmpl = loader.load('info.html')
        return tmpl.generate().render('html', doctype='html')
    
    @cherrypy.expose
    def geo(self,q):
        cherrypy.response.headers['Content-Type']= 'application/json'
        url = "nominatim.openstreetmap.org:80"
        params = urllib.urlencode({
          "q": q.encode("utf-8"),
          "format":"json",
          "polygon": 0,
          "addressdetails" : 1,
          "email" : self.admin_email
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
          "email" : self.admin_email
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
        now_chrone = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        start_chrone = datetime.datetime.strptime(start_date, "%Y%m%d")
        past_seconds = now_chrone.hour * 60 * 60 + now_chrone.minute * 60 + now_chrone.second
        delta = now_chrone - start_chrone
        return {'seconds':past_seconds,'days':delta.days} 
        

total = len( sys.argv )
if total != 2:
    sys.exit("Usage: python server.py {config_file.py}")
if not os.path.exists( os.getcwd() + "/" + sys.argv[1] ):
    raise NameError('Configuration file does not exist')
exec( file( sys.argv[1] ) )
cherrypy.config.update({
    'tools.encode.on': True,
    'tools.encode.encoding': 'utf-8',
    'tools.decode.on': True,
    'tools.trailing_slash.on': True,
    'tools.staticdir.root': os.path.abspath(os.path.dirname(__file__)) + "/web/",
    'server.socket_port': listening_port,
    'server.socket_host': '0.0.0.0'
})
cherrypy.tree.mount(Mumoro(db_type + ":///" + db_params,sys.argv[1],admin_email,web_url), '/', config={
    '/': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'
       },
})
cherrypy.quickstart()

def main():
    print "Goodbye!"
    

