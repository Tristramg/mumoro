import installconfig
import unittest
from sqlalchemy import *
import os.path
import httplib


class TestSequenceFunctions(unittest.TestCase):
    def setUp(self):
        self.import_check = ImportControl()

    def test_nodes(self):
        self.assertEqual(self.import_check.count_nodes(), 17)
        
    def test_edges(self):
        self.assertEqual(self.import_check.count_edges(), 16)

    def test_bike_station(self):
        self.self.assertTrue(self.import_check.count_bike_stations() > 2)

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

    def count_bike_stations():
        bike_stations = Table('bike_stations', self.metadata,
        Column('id_station', Integer, primary_key=True),
        Column('av_bikes', Integer),
        Column('av_slots', Integer),
        Column('name', Text),
        Column('district_name', Text),
        Column('lon', DOUBLE_PRECISION),
        Column('lat', DOUBLE_PRECISION),
        Column('chrone', TIMESTAMP(timezone=False)),
        )
        s = select([func.count("*")], from_obj=[bike_stations])
        rs = s.execute()
        for row in rs:
            total =  int(row[0])
        return total

    def file_exists(f):
        return os.path.exists(f)

    def filter_params_correct(top,bottom,left,right):
        return top >= bottom and right >= left

    def url_is_not_empty(url):
        return url != ""
        
    def url_connects(url):
        try:
             urllib.urlopen(url)
             return True
        except IOError e:
             return False
             
    def url_not_404(domain,app,param):
        headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/xml"}
        p = urllib.urlencode(param)
        conn = httplib.HTTPConnection(domain)
        conn.request("GET", "/"+app)
        r1 = conn.getresponse()
        return r1.status != 404

    def url_has_right(dommain,app,param):
        headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/xml"}
        p = urllib.urlencode(param)
        conn = httplib.HTTPConnection(domain)
        conn.request("GET", "/"+app)
        r1 = conn.getresponse()
        return r1.status != 403
    

    
        
        
