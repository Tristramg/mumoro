import installconfig
import unittest
from sqlalchemy import *


class TestSequenceFunctions(unittest.TestCase):
    def setUp(self):
        self.import_check = ImportControl()

    def test_nodes(self):
        self.assertEqual(self.import_check.count_nodes(), 17)
        
    def test_edges(self):
        self.assertEqual(self.import_check.count_edges(), 16)

if __name__ == '__main__':
    unittest.main()


class ImportControl(self):
    self.db = create_engine( installconfig.db_type + ':///' + installconfig.db_params, echo=True )
    self.metadata = MetaData(db)

    def count_nodes():
        nodes = Table('nodes', metadata,
        Column('id', PGBigInteger, primary_key=True),
        Column('lon', Double),
        Column('lat', Double),
        Column('the_geom', Text),
        )
        s = select([func.count("*")], from_obj=[nodes])
        rs = s.execute()
        for row in rs:
            total =  int(row[0])
        return total

    def count_edges():
        edges = Table('edges', metadata,
        Column('id', Integer, primary_key=True),
        Column('source', PGBigInteger),
        Column('target', PGBigInteger),
        Column('length', Double),
        Column('car', SmallInteger),
        Column('car_rev', SmallInteger),
        Column('bike', SmallInteger),
        Column('bike_rev', SmallInteger),
        Column('foot', SmallInteger),
        Column('the_geom', Text),
        )
        s = select([func.count("*")], from_obj=[edges])
        rs = s.execute()
        for row in rs:
            total =  int(row[0])
        return total
