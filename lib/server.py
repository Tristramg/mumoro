import mumoro
import cherrypy
from cherrypy import request
import simplejson as json
import os
import layer
import bikestations
import time
import config
import shorturl

class HelloWorld:
    def __init__(self):
	c = config.Config()        
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

    def h(self,id):
        hashCheck = shorturl.shortURL()
        hashCheck.getDataFromHash(id)

    match.exposed = True
    path.exposed = True
    bikes.exposed = True
    h.exposed = True;

PATH = os.path.abspath(os.path.dirname(__file__))
cherrypy.tree.mount(HelloWorld(), '/', config={
        '/': {
                'tools.staticdir.on': True,
		'tools.staticdir.dir': PATH + '/static/',
		'tools.staticdir.index': 'index.html',
            },
    })

cherrypy.quickstart()

