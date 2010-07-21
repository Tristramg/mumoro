import os.path
import urllib
import datetime

from sqlalchemy import *
from xml.dom.minidom import parse

def get_text(node):
    return node.childNodes[0].nodeValue

def get_int(node):
    return int(get_text(node))

def get_float(node):
    return float(get_text(node))

class BikeStationImporter():
    def __init__(self, url, name, metadata):
        if not url:
            raise NameError('URL Bike service is empty')
        if not metadata:
            raise NameError('Database connection parameteres are empty')
        self.metadata = metadata
        self.url = url
        self.bike_stations_table = Table(name, self.metadata,
                Column('id_station', Integer, primary_key=True),
                Column('av_bikes', Integer),
                Column('av_slots', Integer),
                Column('name', Text),
                Column('district_name', Text),
                Column('lon', Float),
                Column('lat', Float),
                Column('chrone', Time(timezone=False)),
        )
        self.metadata.create_all()
    def import_data(self):
        self.bike_stations_table.delete().execute()
        xml = urllib.urlopen(self.url)
        doc = parse(xml)
        for station in doc.documentElement.getElementsByTagName("station"):
            if station.nodeType == station.ELEMENT_NODE:
                try:
                    tmp = datetime.datetime.now() 
                    i = self.bike_stations_table.insert()
                    i.execute({'id_station': get_text(station.getElementsByTagName("id")[0]),
                               'av_bikes': get_int(station.getElementsByTagName("bikesavailable")[0]),
                               'av_slots': get_int(station.getElementsByTagName("slotsavailable")[0]),
                               'name': get_text(station.getElementsByTagName("name")[0]),
                               'district_name': get_text(station.getElementsByTagName("district")[0]),
                               'lon': get_float(station.getElementsByTagName("longitude")[0]),
                               'lat': get_float(station.getElementsByTagName("latitude")[0]),
                               'chrone': datetime.time( tmp.hour, tmp.minute ) }
                    )
                except:
                    print 'At least one tag misses: num, name, state, lat, lon, availableSlots, availableBikes, districtName'
    def update_from_db(self):
        self.stations = []
        s = self.bike_stations_table.select()
        rs = s.execute()
        for tmp in rs:
            try:
                s = {
                 'num': str(tmp.id_station),
                 'name': tmp.name.encode("utf-8"),
                 'state': "1",
                 'lat': tmp.lat,
                 'lon': tmp.lon,
                 'availableBikes': tmp.av_bikes,
                 'availableSlots': tmp.av_slots,
                 'districtName': tmp.district_name.encode("utf-8"),
                 'chrone': tmp.chrone.strftime("%H:%M")
                }
                self.stations.append(s)
            except:
                print 'At least one tag misses: num, name, lat, lon, availableSlots, availableBikes, districtName, chrone'
    
    def to_string(self):
        title = '<div id=\'bikes\'><span class=\'smallTitle\'>'
        textRed = '<span class=\'bikeRed\'>'
        textOrange = '<span class=\'bikeOrange\'>'
        tinyText = '<span class=\'tinyText\'>'
        res = ''
        for s in self.stations:
            res += '%f\t%f\t' % (s['lat'], s['lon'])
            res += (title + s['name'] + ' (' + s['num'] + ')</span><br/>\t')
            if (s['state'] == 0):
                res += ( textRed + 'Station supports only bike deposits</span><br/>')
            elif (s['availableBikes'] == 0):
                res += ( textRed + 'No available bikes</span><br/>')
            elif (s['availableBikes'] < 3):
                res += ( textOrange + '%i Available bikes</span><br/>' % s['availableBikes'])
            else:
                res += ( title + '%i Available bikes</span><br/>' % s['availableBikes'])
            if (s['availableSlots'] == 0):
                res += ( textRed + 'No available deposit slots</span><br/>')
            elif (s['availableSlots'] < 3):
                res += ( textOrange + '%i Available slots</span><br/>' % s['availableSlots'])
            else:
                res += ( title + '%i Available slots</span><br/>' % s['availableSlots'] )
            res += ('<br/>' + tinyText + 'Latest update at ' + s['chrone'] + '</span>')
            res += ('<br/>' + tinyText + 'Click again to close</span></div>\t')
            if (s['availableSlots'] == 0 or s['availableBikes'] == 0 or ['state'] == 0):
                res += ('img/bike.station.red.png\t18,25\t-8,-25\n')
            elif (s['availableSlots'] < 3 or s['availableBikes'] < 3):
                res += ('img/bike.station.orange.png\t18,25\t-8,-25\n')
            else:
                res += ('img/bike.station.green.png\t18,25\t-8,-25\n')
        return res

#if __name__ == "__main__":
#    engine = create_engine('sqlite:////home/ody/takis.db')
#    metadata = MetaData(bind = engine)
#    u = "http://data.keolis-rennes.com/xml/?version=1.0&key=UAYPAP0MHD482NR&cmd=getstation&param[request]=all"
#    v = BikeStationImporter( u,'1',metadata)
#    v.import_data()
#    v.update_from_db()    
#    print v.to_string()
#    print "Done!"
