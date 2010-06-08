# -*- coding: utf-8 -*-

from lib.core import mumoro
from lib import layer 
from lib import bikestations as bikestations
from web import config
from web import shorturl

import cherrypy
import operator
import pickle
import sys
import simplejson as json
import os
import time
import urllib
import httplib

from cherrypy import request
from genshi.template import TemplateLoader

loader = TemplateLoader(
    os.path.join(os.path.dirname(__file__), 'web/templates'),
    auto_reload=True
)

class Mumoro:
    def __init__(self,data):
        c = config.Config()
        self.data = data       
        foot = layer.Layer('foot', mumoro.Foot, {'nodes': c.tableNodes, 'edges': c.tableEdges}, c)
        foot2 = layer.Layer('foot2', mumoro.Foot, {'nodes': c.tableNodes, 'edges': c.tableEdges}, c)
        bike = layer.Layer('bike', mumoro.Bike, {'nodes': c.tableNodes, 'edges': c.tableEdges}, c)
        car = layer.Layer('car', mumoro.Car, {'nodes': c.tableNodes, 'edges': c.tableEdges}, c)
        self.stations = bikestations.VeloStar(False, c)
        self.timestamp = time.time()
        e = mumoro.Edge()
        e.mode_change = 1
        e.duration = mumoro.Duration(60);
        e2 = mumoro.Edge()
        e2.mode_change = 0
        e2.duration = mumoro.Duration(30);

        self.g = layer.MultimodalGraph([foot, bike, car, foot2])
        self.g.connect_nodes_from_list(foot, bike, self.stations.stations, e, e2)
        e.mode_change = 0
        e.duration = mumoro.Duration(0)
        self.g.connect_same_nodes(car, foot2, e)
        self.g.connect_same_nodes(foot2, car, e)


    @cherrypy.expose
    def path(self, slon, slat, dlon, dlat):
        start = self.g.match('foot', float(slon), float(slat))
        car_start = self.g.match('foot2', float(slon), float(slat))
        dest = self.g.match('foot', float(dlon), float(dlat))
        car_dest = self.g.match('foot2', float(dlon), float(dlat))

        cherrypy.response.headers['Content-Type']= 'application/json'
        p = mumoro.martins(int(start), int(dest), self.g.graph, 30000, mumoro.mode_change, mumoro.line_change)
        p_car = mumoro.martins(int(car_start), int(car_dest), self.g.graph, 30000)
        if len(p_car) == 1:
            p_car[0].cost.append(0)
            p_car[0].cost.append(0)
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
                if coord == None:
                    print node
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
        if time.time() > self.timestamp + 60 * 5:
            print "Updating bikestations"
            self.stations = bikestations.VeloStar(False, c)
            print "Done !"
        str = self.stations.to_string()
        print "Got string"
        return str;

    @cherrypy.expose
    def addhash(self,mlon,mlat,zoom,slon,slat,dlon,dlat,saddress,daddress,snode,dnode):
        cherrypy.response.headers['Content-Type']= 'application/json'
        hashAdd = shorturl.shortURL()
        hmd5 =hashAdd.addRouteToDatabase(mlon,mlat,zoom,slon,slat,dlon,dlat,saddress,daddress,snode,dnode)
        if( len(hmd5) > 0 ):
            ret = {
                'h': hmd5
            }
            return json.dumps(ret)
        else:
            return '{"error": "Add to DB failed"}'

    @cherrypy.expose
    def h(self,id):
        hashCheck = shorturl.shortURL()
        res = hashCheck.getDataFromHash(id)
        if( len(res) > 0 ):
            return self.index(True,res)
        else:
            return self.index(False,res)

    @cherrypy.expose
    def index(self,fromHash=False,hashData=[]):
        c = config.Config()        
        tmpl = loader.load('index.html')
        if( not fromHash ):
            return tmpl.generate(fromHash='false',lonMap=-1.68038,latMap=48.11094,zoom=15,lonStart=0.0,latStart=0.0,lonDest=0.0,latDest=0.0,addressStart='',addressDest='',s_node=1,d_node=1,hashUrl=c.urlHash).render('html', doctype='html')
        else:
            return tmpl.generate(fromHash='true',lonMap=hashData[2],latMap=hashData[3],zoom=hashData[1],lonStart=hashData[4],latStart=hashData[5],lonDest=hashData[6],latDest=hashData[7],addressStart=hashData[8].decode('utf-8'),addressDest=hashData[9].decode('utf-8'),s_node=hashData[11],d_node=hashData[12],hashUrl=c.urlHash).render('html', doctype='html')

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
          "email" : "odysseas.gabrielides@gmail.com"
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
                        id_node = self.match(lon,lat)
                        if id_node:
                                node_error = ""
                                is_covered = True
                        else:
                                node_error = "match failed"
                else:
                        id_node = 0
                        node_error = "not covered area"
        else:
                cord_error = "geocoding failed"
                lon = 0
                lat = 0
                display_name = ""
                id_node = 0             
                node_error = "match failed because geocoding failed"
        data = {
                'node': id_node,
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
          "email" : "odysseas.gabrielides@gmail.com"
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
                        id_node = self.match(float(lon),float(lat))
                        if id_node:
                                node_error = ""
                                is_covered = True
                        else:
                                node_error = "match failed"
                else:
                        id_node = 0
                        node_error = "not covered area"
        else:
                cord_error = "geocoding failed"
                display_name = ""
                id_node = 0             
                node_error = "match failed because revgeocoding failed"
        data = {
                'node': id_node,
                'display_name': display_name,
                'node_error': node_error,
                'cord_error': cord_error,
                'is_covered': is_covered
        }
        return json.dumps(data)

    def arecovered(self,lon,lat):
        #Coverage area of Rennes. Hardcored for simplicity      
        if( lon <= -1.73113 or lon >= -1.56359 or lat <= 48.07448 or lat >= 48.14532 ):
            return False        
        else:
            return True   
        
if __name__ == '__main__':
    c = config.Config()
    data = {} # We'll replace this later
    cherrypy.config.update({
        'tools.encode.on': True,
        'tools.encode.encoding': 'utf-8',
        'tools.decode.on': True,
        'tools.trailing_slash.on': True,
        'tools.staticdir.root': os.path.abspath(os.path.dirname(__file__)) + "/web/",
        'server.socket_port': c.cpPort,
        'server.socket_host': '0.0.0.0'

    })
    cherrypy.tree.mount(Mumoro(data), '/', config={
        '/': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': 'static'
           },
    })
    cherrypy.quickstart()

