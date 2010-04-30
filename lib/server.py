# -*- coding: utf-8 -*-

import mumoro
import cherrypy
import operator
import pickle
import sys
import simplejson as json
import os
import layer
import bikestations
import time
import config
import shorturl

from cherrypy import request
from genshi.template import TemplateLoader

loader = TemplateLoader(
    os.path.join(os.path.dirname(__file__), 'templates'),
    auto_reload=True
)

class HelloWorld:
    def __init__(self,data):
	c = config.Config()
	self.data = data       
	foot = layer.Layer('foot', mumoro.Foot, {'nodes': c.tableNodes, 'edges': c.tableEdges})
        bike = layer.Layer('bike', mumoro.Bike, {'nodes': c.tableNodes, 'edges': c.tableEdges})
        car = layer.Layer('car', mumoro.Car, {'nodes': c.tableNodes, 'edges': c.tableEdges})
#        bart = layer.GTFSLayer('bart', 'google_transit.zip', dbname='bart.db') 
#        muni = layer.GTFSLayer('muni', 'san-francisco-municipal-transportation-agency_20091125_0358.zip', dbname='muni.db') 

        #pt = layer.GTFSLayer('muni', 'pt')
        self.stations = bikestations.VeloStar()
        self.timestamp = time.time()
        #print request.params['username']
        e = mumoro.Edge()
        e.mode_change = 1
        e.duration = mumoro.Duration(60);
        e2 = mumoro.Edge()
        e2.mode_change = 0
        e2.duration = mumoro.Duration(30);

        self.g = layer.MultimodalGraph([foot, bike, car])
        self.g.connect_nodes_from_list(foot, bike, self.stations.stations, e, e2)
        #self.g.connect_nearest_nodes(pt, foot, e, e2)


    def path(self, slon, slat, dlon, dlat):
        start = self.g.match('foot', float(slon), float(slat))
        print start
        car_start = self.g.match('car', float(slon), float(slat))
        print car_start
        dest = self.g.match('foot', float(dlon), float(dlat))
        print dest
        car_dest = self.g.match('car', float(dlon), float(dlat))
        print car_dest
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
    
    def match(self, lon, lat):
        cherrypy.response.headers['Content-Type']= 'application/json'
        id = self.g.match('foot', lon, lat)
        if id:
            ret = {'node': id}
            return json.dumps(ret)
        else:
            return '{"error": "No node found"}'

    def bikes(self):
        if time.time() > self.timestamp + 60 * 5:
            print "Updating bikestations"
            self.stations = bikestations.VeloStar()
        return self.stations.to_string()

    def addhash(self,mlon,mlat,zoom,slon,slat,dlon,dlat,saddress,daddress):
        hashAdd = shorturl.shortURL()
	hmd5 =hashAdd.addRouteToDatabase(mlon,mlat,zoom,slon,slat,dlon,dlat,saddress,daddress)
        if( len(hmd5) > 0 ):
            ret = {
                'h': hmd5
            }
            return json.dumps(ret)
        else:
            return '{"error": "Add to DB failed"}'

    def h(self,id):
        hashCheck = shorturl.shortURL()
        res = hashCheck.getDataFromHash(id)
        if( len(res) > 0 ):
            return self.index(True,res)
        else:
            return self.index(False,res)

    @cherrypy.expose
    def index(self,fromHash=False,hashData=[]):
        tmpl = loader.load('index.html')
        if( not fromHash ):
            return tmpl.generate(fromHash='false',lonMap=-1.68038,latMap=48.11094,zoom=15,lonStart=0.0,latStart=0.0,lonDest=0.0,latDest=0.0,addressStart='',addressDest='').render('html', doctype='html')
        else:
            return tmpl.generate(fromHash='true',lonMap=hashData[2],latMap=hashData[3],zoom=hashData[1],lonStart=hashData[4],latStart=hashData[5],lonDest=hashData[6],latDest=hashData[7],addressStart=hashData[8].decode('utf-8'),addressDest=hashData[9].decode('utf-8')).render('html', doctype='html')

    match.exposed = True
    path.exposed = True
    bikes.exposed = True
    h.exposed = True
    index.exposed = True
    addhash.exposed = True

def main(filename):
    data = {} # We'll replace this later
    cherrypy.config.update({
        'tools.encode.on': True, 'tools.encode.encoding': 'utf-8',
        'tools.decode.on': True,
        'tools.trailing_slash.on': True,
        'tools.staticdir.root': os.path.abspath(os.path.dirname(__file__)),
    })
    cherrypy.tree.mount(HelloWorld(data), '/', config={
        '/': {
                'tools.staticdir.on': True,
		'tools.staticdir.dir': 'static'
           },
    })
    cherrypy.quickstart()
if __name__ == '__main__':
    main(sys.argv[1])

