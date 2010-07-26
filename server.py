#  -*- coding: utf-8 -*-

from lib.core import mumoro
from lib.core.mumoro import Bike, Car, Foot, PublicTransport
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

start_layer =  []
dest_layer = []

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
    for row in rs:
         nd = row[0]
    s = mumoro_metadata.select((mumoro_metadata.c.origin == filename) & (mumoro_metadata.c.node_or_edge == 'Edges'))
    rs = s.execute()
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

def set_starting_layer( layer ):
    if not layer:
        raise NameError('Empty layer')
    start_layer.append( layer )

def set_destination_layer( layer ):
    if not layer:
        raise NameError('Empty layer')
    dest_layer.append( layer )

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
def connect_layers_on_nearest_nodes( layer1 , layer2, cost ):
    if not layer1 or not layer2 or not cost:
        raise NameError('One or more paramaters are empty')
    nearest_nodes_connection_array.append( { 'layer1':layer1, 'layer2':layer2, 'cost':cost } )

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
        for i in range( len( layer_array ) ):
            layers.append( layer_array[i]['layer'] )
        if not start_layer:
                raise NameError('There is no starting layer')
        if not dest_layer:
                raise NameError('There is no destination layer')
        for i in range( len( layer_array ) ):
            for j in range( len( layer_array ) ):
                if i != j:
                    if layer_array[i]['name'] == layer_array[j]['name']:
                        raise NameError('Layers can not have the same name')
        self.engine = create_engine(db_string)
        self.metadata = MetaData(bind = self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.total_bike_stations = len( bike_stations_array )
        self.bike_stations = []
        if self.total_bike_stations > 0:
            for i in range( self.total_bike_stations ):
                  self.bike_stations.append( bikestations.BikeStationImporter(bike_stations_array[i]['url_api'],
                                                                           bike_stations_array[i]['table'],
                                                                           self.metadata) )
            for i in range( self.total_bike_stations ):
                self.bike_stations[i].update_from_db()
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
            total_same_nodes_connections = len( same_nodes_connection_array )
            if total_same_nodes_connections > 0:
                for i in range( total_same_nodes_connections ):
                    self.g.connect_same_nodes( same_nodes_connection_array[i]['layer1']['layer'],
                                               same_nodes_connection_array[i]['layer2']['layer'],
                                               same_nodes_connection_array[i]['cost'] )
            total_nearest_nodes_connections = len( nearest_nodes_connection_array )
            if total_nearest_nodes_connections > 0:
                for i in range( total_nearest_nodes_connections ):
                    self.g.connect_nearest_nodes( nearest_nodes_connection_array[i]['layer1']['layer'],
                                               nearest_nodes_connection_array[i]['layer2']['layer'],
                                               nearest_nodes_connection_array[i]['cost'] )
            total_nodes_list_connections = len( nodes_list_connection_array )
            if total_nodes_list_connections > 0:
                for i in range( total_nodes_list_connections ):
                   try:
                       nodes_list_connection_array[i]['node_list']['url_api']
                       print 'Assuming that the nodes list are bike stations'
                       for j in range( self.total_bike_stations ):
                           if self.bike_stations[j].url == nodes_list_connection_array[i]['node_list']['url_api']:
                               self.g.connect_nodes_from_list( nodes_list_connection_array[i]['layer1']['layer'],
                                              nodes_list_connection_array[i]['layer2']['layer'],
                                              self.bike_stations[j].stations,
                                              nodes_list_connection_array[i]['cost1'],
                                              nodes_list_connection_array[i]['cost2'] )
                               break
                   except KeyError:
                       try:
                           nodes_list_connection_array[i]['node_list']['layer']
                           print 'Assuming that the nodes list is a public transport layer'
                           self.g.connect_nodes_from_list( nodes_list_connection_array[i]['layer1']['layer'],
                                              nodes_list_connection_array[i]['layer2']['layer'],
                                              nodes_list_connection_array[i]['node_list']['layer'].nodes(),
                                              nodes_list_connection_array[i]['cost1'],
                                              nodes_list_connection_array[i]['cost2'] )
                       except KeyError:
                           raise NameError('Can not connect layers from the node list')
            md5_config_checksum = md5_of_file( file( config_file ) )
            self.g.save( md5_config_checksum + '.dump' )
            i = self.config_table.insert()
            i.execute({'config_file': config_file, 'md5': md5_config_checksum, 'binary_file': md5_config_checksum + '.dump'})

    @cherrypy.expose
    def path(self, slon, slat, dlon, dlat):
        start = self.g.match(start_layer[0]['name'], float(slon), float(slat))
        dest = self.g.match(dest_layer[0]['name'], float(dlon), float(dlat))
        cherrypy.response.headers['Content-Type']= 'application/json'
        p = mumoro.martins(start, dest, self.g.graph,30000, 7, mumoro.mode_change, mumoro.line_change)
        p_car = []#mumoro.martins(car_start, car_dest, self.g.graph,0, 30000)
        if len(p_car) == 1:
            p_car[0].cost.append(0)
            p_car[0].cost.append(0)
            print p_car[0].cost[0]
            p = p + p_car
        if len(p) == 0:
            return json.dumps({'error': 'No route found'})
        
        ret = {
                'objectives': ['Duration', 'Mode changes', 'Line changes'],
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
    def match(self, lon, lat):
        return self.g.match('foot', lon, lat)

    @cherrypy.expose
    def bikes(self):
        if self.total_bike_stations > 0:
            if time.time() > self.timestamp + 60 * 5:
                print "Updating bikestations"
                for i in range( self.total_bike_stations ):
                    self.bike_stations[i].import_data()
                print "Done !"
            for i in range( self.total_bike_stations ):
                self.bike_stations[i].update_from_db()
            res = 'lat\tlon\ttitle\tdescription\ticon\ticonSize\ticonOffset\n'
            for i in range( self.total_bike_stations ):
                res += self.bike_stations[i].to_string()
            print "Got string"
            return res;
        else:
            print "No bike stations imported so no string available to generate"
            return None

    @cherrypy.expose
    def addhash(self,mlon,mlat,zoom,slon,slat,dlon,dlat,saddress,daddress):
        cherrypy.response.headers['Content-Type']= 'application/json'
        hashAdd = shorturl.shortURL(self.metadata)
        hmd5 =hashAdd.addRouteToDatabase(mlon,mlat,zoom,slon,slat,dlon,dlat,saddress,daddress)
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
            a = start_layer[0]['layer'].average()
            b = start_layer[0]['layer'].borders()
            return tmpl.generate(fromHash='false',lonMap=a['avg_lon'],latMap=a['avg_lat'],zoom=14,lonStart=b['min_lon'],latStart=b['min_lat'],lonDest=b['max_lon'],latDest=b['max_lat'],addressStart='',addressDest='',hashUrl=self.web_url,layers=t).render('html', doctype='html')
        else:
            return tmpl.generate(fromHash='true',lonMap=hashData[2],latMap=hashData[3],zoom=hashData[1],lonStart=hashData[4],latStart=hashData[5],lonDest=hashData[6],latDest=hashData[7],addressStart=hashData[8].decode('utf-8'),addressDest=hashData[9].decode('utf-8'),hashUrl=self.web_url,layers=l).render('html', doctype='html')


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
        for i in range( len( layer_array ) ):
            b = layer_array[i]['layer'].borders()
            if lon >= b['min_lon'] and lon <= b['max_lon'] and lat >= b['min_lat'] and lat <= b['max_lat']:
                return True
        return False

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
    
