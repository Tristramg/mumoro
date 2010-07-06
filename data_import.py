import configuration_script
import os.path
import osm4routing
from lib import gtfs_reader
from lib.datastructures import *
from sqlalchemy import *
from sqlalchemy.orm import mapper, sessionmaker, clear_mappers

def Class Importer():
    def __init__(self):
        self.db_string = configuration_script.db_type + ":///" + configuration_script.db_params
        self.engine = create_engine(self.db_string)
        self.metadata = MetaData(bind = engine)
        self.mumoro_metadata = Table('metadata', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('node_or_edge', String),
                Column('name', String),
                Column('origin', String)
                )
        self.metadata.create_all()
        mapper(Metadata, self.mumoro_metadata)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def init_mappers(self):
        clear_mappers()
        mapper(Metadata, self.mumoro_metadata)

    #Loads an osm (compressed of not) file and insert data into database.Optional : can filter a region with top,left,bottom and right arguments.
    def import_street_data( filename, filter = False, top = 0.0, left = 0.0, bottom = 0.0, right = 0.0 ):
    if not os.path.exists( filename ):
        raise NameError('File does not exist')
    if filter:
        if top <= bottom or right <= left:
            raise NameError('Top and right must be bigger than bottom and left')
    nodes = Metadata("OSM nodes", "Nodes", filename)
    edges = Metadata("OSM edges", "Edges", filename)
    self.session.add(nodes)
    self.session.add(edges)
    self.session.commit()
    osm4routing.parse(filename, self.db_string, str(nodes.id), str(edges.id)) 
    self.init_mappers()

    #Loads muncipal data file 
    #( 3 cases : GTFS format (Call TransitFeed), Trident format (Call Chouette), Other : manual implementation ) and insert muncipal data into database.
    #start_date & end_date in this format : 'YYYYMMDD'
    def import_municipal_data(self, filename, start_date, end_date, network_name = "GTFS"):
        if not os.path.exists( file ):
            raise NameError('File does not exist')
        nodes2 = Metadata(network_name, "Nodes", filename)
        self.session.add(nodes2)
        self.session.commit()
        mapper(PT_Node, create_pt_nodes_table(str(nodes2.id), self.metadata))
        edges2 = Metadata(network_name, "Edges", filename)
        self.session.add(edges2)
        self.session.commit()
        mapper(PT_Edge, create_pt_edges_table(str(edges2.id), self.metadata))
        self.session.commit()
        gtfs_reader.convert(filename, self.session, start_date, end_date)
        self.init_mappers()
    
     #Loads a bike service API ( from already formatted URL ). Insert bike stations in database and enables schedulded re-check.
     def import_bike_service( url ):
         pass



#Loads data from previous inserted data and creates a layer used in multi-modal graph
def load_layer( data, layer_name, layer_mode ):

#Creates a transit cost variable, including the duration in seconds of the transit and if the mode is changed
def cost( duration, mode_changed ):

#Connects 2 given layers on same nodes with the given cost(s)
def connect_layers_same_nodes( layer1, layer2, cost, cost2 = 0 ):

#Connect 2 given layers on a node list (arg 3 which should be the returned data from import_municipal_data or import_bike_service) with the given cost(s)
def connect_layers_from_node_list( layer1, layer2, node_list, cost, cost2 = 0 ):

