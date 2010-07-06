import osm4routing
from lib import gtfs_reader
from lib.datastructures import *
from sqlalchemy import *
from sqlalchemy.orm import mapper, sessionmaker, clear_mappers

class Importer():
    def __init__(self, db_string):
        self.db_string = db_string
        engine = create_engine(db_string)
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



    def import_osm(self, filename):
        nodes = Metadata("OSM nodes", "Nodes", filename)
        edges = Metadata("OSM edges", "Edges", filename)
        self.session.add(nodes)
        self.session.add(edges)
        self.session.commit()
        osm4routing.parse(filename, self.db_string, str(nodes.id), str(edges.id)) 
        self.init_mappers()


    def import_gtfs(self, filename, start_date, end_date, network_name = "GTFS"):
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
    

if __name__ == "__main__":
    db_string = 'sqlite:///blah.db'
    osm_file = "rennes.osm.bz2"
    bart_file = "bart.zip"
    start_date = "20100701"
    end_date = "20101031"
    i = Importer(db_string)
    i.import_osm(osm_file)
    i.import_gtfs(bart_file, start_date, end_date, "BART")
    i.import_gtfs(bart_file, start_date, end_date, "BART2")

