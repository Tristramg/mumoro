import osm4routing
import gtfs_reader
import uuid
from lib.datastructures import *
from sqlalchemy import *
from sqlalchemy.orm import mapper, sessionmaker

def import_osm(filename, db_string, nodes_table, edges_table):
    osm4routing.parse(filename, db_string, nodes_table, edges_table) 


if __name__ == "__main__":
    db_string = 'sqlite:///blah.db'
    engine = create_engine(db_string)
    metadata = MetaData(bind = engine)

    mumoro_metadata = Table('metadata', metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('origin', String)
            )
    
    metadata.create_all()
    mapper(Metadata, mumoro_metadata)

    Session = sessionmaker(bind=engine)
    session = Session()

    osm_file = "rennes.osm.bz2"
    nodes = Metadata("OSM nodes", osm_file)
    edges = Metadata("OSM edges", osm_file)
    session.add(nodes)
    session.add(edges)
    session.commit()
    import_osm("rennes.osm.bz2", db_string, str(nodes.id), str(edges.id))

    bart_file = "bart.zip"
    start_date = "20100701"
    end_date = "20101031"
    nodes2 = Metadata("Bart", bart_file)
    edges2 = Metadata("Bart", bart_file)
    session.add(nodes2)
    session.add(edges2)
    session.commit()
#    gtfs_reader.convert(bart_file, str(nodes2.id), str(edges2.id), start_date, end_date)

#    n1 = create_nodes_table('nodes', metadata)
#    n2 = create_nodes_table('nodes2', metadata)
#    e1 = create_edges_table('edges', metadata)
#    e2 = create_edges_table('edges2', metadata)
#    metadata.create_all()
#    mapper(Node, n1)
#    session.add(Node("blah", 1, 2))
#    session.commit()

