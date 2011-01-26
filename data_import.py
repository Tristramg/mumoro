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

import sys
from lib.core.mumoro import *
from lib.core import mumoro
import osm4routing
from lib import bikestations, gtfs_reader, kalkati_reader
import os.path
from lib.datastructures import *
from sqlalchemy import *
from sqlalchemy.orm import mapper, sessionmaker, clear_mappers
import datetime
import csv

street_data_array = []
municipal_data_array = []
kalkati_data_array = []
freq_data_array = []
bike_service_array = []


class Importer():
    def __init__(self,db_type,db_params, start_date, end_date):
        if not db_type or not db_params:
            raise NameError('Database connection parameters are empty')
        self.db_string = db_type + ":///" + db_params
        print "Connection string is : " + self.db_string        
        self.engine = create_engine(self.db_string)
        self.metadata = MetaData(bind = self.engine)
        self.mumoro_metadata = Table('metadata', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('node_or_edge', String),
                Column('name', String),
                Column('origin', String)
                )
        self.metadata.create_all()
        mapper(Metadata, self.mumoro_metadata)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        for f in street_data_array:
                self.import_osm( f )

        if municipal_data_array:
            is_date_valid( start_date )
            is_date_valid( end_date )
            for m in municipal_data_array:
                self.import_gtfs( m['file'], start_date, end_date, m['network'] )

        for b in bike_service_array:
            self.import_bike( b['url_api'], b['service_name'] )


        if kalkati_data_array:
            is_date_valid( start_date )
            is_date_valid( end_date )
            for m in kalkati_data_array:
                self.import_kalkati( m['file'], start_date, end_date, m['network'] )

        for f in freq_data_array:
            self.import_freq(f['line_name'], f['nodesf'], f['linesf'], start_date, end_date)



    def init_mappers(self):
        clear_mappers()
        mapper(Metadata, self.mumoro_metadata)

    def import_osm( self, filename ):
        print "Adding street data from " + filename
        nodes = Metadata("OSM nodes", "Nodes", filename)
        edges = Metadata("OSM edges", "Edges", filename)
        self.session.add(nodes)
        self.session.add(edges)
        self.session.commit()
        osm4routing.parse(filename, self.db_string, str(edges.id), str(nodes.id) ) 
        self.init_mappers()
        print "Done importing street data from " + filename
        print "---------------------------------------------------------------------"

    def import_gtfs(self, filename, start_date, end_date, network_name = "GTFS"):
        print "Adding municipal data from " + filename
        print "From " + start_date + " to " + end_date + " for " + network_name + " network"

        stop_areas = Metadata(network_name, "StopAreas", filename)
        self.session.add(stop_areas)
        self.session.commit()
        mapper(PT_StopArea, create_pt_stop_areas_table(str(stop_areas.id), self.metadata))

        nodes2 = Metadata(network_name, "Nodes", filename)
        self.session.add(nodes2)
        self.session.commit()
        mapper(PT_Node, create_pt_nodes_table(str(nodes2.id), self.metadata, str(stop_areas.id)))
        
        services = Metadata(network_name, "Services", filename)
        self.session.add(services)
        self.session.commit()
        mapper(PT_Service, create_services_table(str(services.id), self.metadata))

        lines = Metadata(network_name, "Lines", filename)
        self.session.add(lines)
        self.session.commit()
        mapper(PT_Line, create_pt_lines_table(str(lines.id), self.metadata))

        edges2 = Metadata(network_name, "Edges", filename)
        self.session.add(edges2)
        self.session.commit()
        mapper(PT_Edge, create_pt_edges_table(str(edges2.id), self.metadata, str(services.id), str(lines.id)))
        self.session.commit()

        gtfs_reader.convert(filename, self.session, start_date, end_date)
        self.init_mappers()
        print "Done importing municipal data from " + filename + " for network '" + network_name + "'"
        print "---------------------------------------------------------------------"
    
    def import_kalkati(self, filename, start_date, end_date, network_name = "GTFS"):
        print "Adding municipal data from " + filename
        print "From " + start_date + " to " + end_date + " for " + network_name + " network"
        nodes2 = Metadata(network_name, "Nodes", filename)
        self.session.add(nodes2)
        self.session.commit()
        mapper(PT_Node, create_pt_nodes_table(str(nodes2.id), self.metadata))

        services = Metadata(network_name, "Services", filename)
        self.session.add(services)
        self.session.commit()
        mapper(PT_Service, create_services_table(str(services.id), self.metadata))

        edges2 = Metadata(network_name, "Edges", filename)
        self.session.add(edges2)
        self.session.commit()
        mapper(PT_Edge, create_pt_edges_table(str(edges2.id), self.metadata, str(services.id)))
        self.session.commit()

        kalkati_reader.convert(filename, self.session, start_date, end_date)
        self.init_mappers()
        print "Done importing municipal data from " + filename + " for network '" + network_name + "'"
        print "---------------------------------------------------------------------"

    def import_bike(self, url, name):
        print "Adding public bike service from " + url
        bike_service = Metadata(name, "bike_stations", url )
        self.session.add(bike_service)
        self.session.commit()
        i = bikestations.BikeStationImporter( url, str(bike_service.id), self.metadata)
        i.import_data()
        self.init_mappers()
        print "Done importing bike service '" + name + "'"
        print "---------------------------------------------------------------------"

    def import_freq(self, line_name, nodesf, linesf, start_date, end_date):
        print "Importing a frequency PT Node File"
        stop_areas_table = Metadata(line_name, "Stop Areas", line_name)
        self.session.add(stop_areas_table)
        self.session.commit()
        create_pt_stop_areas_table(str(stop_areas_table.id), self.metadata)

        nodes_table = Metadata(line_name, "Nodes", line_name)
        self.session.add(nodes_tables)
        self.session.commit()
        create_pt_nodes_table(str(nodes_table.id), self.metadata)

        edges_table = Metadata(line_name, "Edges", line_name)
        self.session.add(edges_table)
        self.session.commit()
        create_pt_edges_table(str(edges_table.id), self.metadata)

        services_table = Metadata(line_name, "Services", line_name)
        self.session.add(services_table)
        self.session.commit()
        create_services_table(str(services_table.id), self.metadata)

        line_table = Metadata(line_name, "Lines", line_name)
        self.session.add(line_table)
        self.session.commit()
        create_pt_lines_table(str(line_name.id), self.metadata)

        # On crée un unique service toujours valide pour ne pas s'embêter
        start_date = datetime.datetime.strptime(start_date, "%Y%m%d")
        end_date = datetime.datetime.strptime(end_date, "%Y%m%d")
        service = '1' * (end_date - start_date).days()
        self.session.add(Services(0, service))

        nodes = csv.reader(open(nodef, 'r'), delimiter=',')
        # Pour chaque nœud on crée un stop_area
        #format de nodes : Id, Nom, lon, lat
        nodes_count = 0
        nodes_map
        for n in nodes:
            session.add(PT_StopArea(n[0], n[1]))
            self.session.add(PT_Node(n[0], n[2], n[3], 0, str(nodes_count)))
            nodes_map[n[0]] = nodes_count

        lines = csv.reader(open(linesf, 'r'), delimiter=',')
        # format de edges : nom_ligne, intervalle en secs, heure_debut, heure_fin, tps_moyen, id_noed1, id_noed2 etc.
        # penser à faire deux ligne selon les sens
        # on peut varier la fréquence selon l'heure de la journée !
        # attention !!! Ne permet pas de dépasser minuit
        # les heures de début et de fin sont en secondes depuis minuit, ex 28800 pour dire 8h du matin, c'est la période sur laquelle est définie la fréquence
        # tps_moyen est le temps moyen en secondes entre deux arrêts. Pas moyen d'avoir plus fin
        lines_count = 0
        for l in lines:
            self.session.add(PT_Line(l[0], l[0], l[0], "#0000AA", '#FFFFFF', line_name))
            tps_moyen = int(l[4])
            lines_count += 1
            for departure in range(int(l[2]), int(l[3]), int(l[1])):
                prev_stop = nodes_map[l[5]]
                for i in range(6, len(l) - 1):
                    current_node = nodes_map[l[i]]
                    self.session.add(PT_Edge(prev_stop, current_node, 0, departure, departure + tps_moyen, 0, "Metro", str(lines_count)))
                    prev_stop = current_node
        self.session.commit()
        self.init_mappers()
        print "Done importing frequency data"
        print "---------------------------------------------------------------------"


#Loads an osm (compressed of not) file and insert data into database
def import_street_data( filename ):
    if not os.path.exists( filename ):
        raise NameError('File does not exist')
    street_data_array.append( filename )

# Loads public transport data from GTFS file format
def import_gtfs_data( filename, network_name = "Public transport"):
    if not os.path.exists( filename ):
        raise NameError('File does not exist')
    municipal_data_array.append( {'file': filename, 'network': network_name } )

# Loads public transport data from Kalkati file format
def import_kalkati_data( filename, network_name = "Public transport"):
    if not os.path.exists( filename ):
        raise NameError('File does not exist')
    kalkati_data_array.append( {'file': filename, 'network': network_name } )


#Loads a bike service API ( from already formatted URL ). Insert bike stations in database and enables schedulded re-check.
def import_bike_service( url, name ):
    if not url:
        raise NameError('Enter an url')
    bike_service_array.append( {'url_api': url, 'service_name': name } )

# Charge les données de transport en commun sous forme de fréquence
def import_freq(self, line_name, nodesf, linesf):
    freq_data_array.append({'line_name': linename, 'nodesf': nodesf, 'linesf': linesf})

#Loads data from previous inserted data and creates a layer used in multi-modal graph
def street_layer(data, name, color, mode):
    pass

def public_transport_layer(data, name, color):
    pass

def paths( starting_layer, destination_layer, objectives ):
    pass


def set_starting_layer( layer ):
    pass

def set_destination_layer( layer ):
    pass

#Creates a transit cost variable, including the duration in seconds of the transit and if the mode is changed
def cost( duration, mode_change ):
    pass

#Connects 2 given layers on same nodes with the given cost(s)
def connect_layers_same_nodes( layer1, layer2, cost ):
    pass

#Connect 2 given layers on a node list (arg 3 which should be the returned data from import_municipal_data or import_bike_service) with the given cost(s)
def connect_layers_from_node_list( layer1, layer2, node_list, cost, cost2 = None ):
    pass

#Connect 2 given layers on nearest nodes
def connect_layers_on_nearest_nodes( layer1 , layer2, cost, cost2 ):
    pass

def is_date_valid( date ):
   date = datetime.datetime.strptime(date, "%Y%m%d")

def main():
    total = len( sys.argv )
    if total != 2:
        sys.exit("Usage: python data_import.py {config_file.py}")
    if not os.path.exists( os.getcwd() + "/" + sys.argv[1] ):
        raise NameError('Configuration file does not exist')
    exec( file( sys.argv[1] ) )
    Importer(db_type,db_params, start_date, end_date)

if __name__ == "__main__":
    main()

