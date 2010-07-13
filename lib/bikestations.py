import os.path
import urllib
import datetime
import time

from sqlalchemy import *
from sqlalchemy.orm import mapper, sessionmaker, clear_mappers
from xml.dom.minidom import parse

def get_text(node):
    return node.childNodes[0].nodeValue

def get_int(node):
    return int(get_text(node))

def get_float(node):
    return float(get_text(node))

class BikeStationImporter():
    def __init__(self, url, db_string):
        if not url:
            raise NameError('URL Bike service is empty')
        if not db_string:
            raise NameError('Database connection string is empty')
        self.engine = create_engine(db_string)
        self.metadata = MetaData(bind = self.engine)
        self.bike_stations_table = Table('bike_stations', self.metadata,
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
        mapper(BikeStation, self.bike_stations_table) 
        xml = urllib.urlopen(url)
        doc = parse(xml)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        for station in doc.documentElement.getElementsByTagName("station"):
            if station.nodeType == station.ELEMENT_NODE:
                try:
                    new_bike_station = BikeStation(
                        get_text(station.getElementsByTagName("id")[0]),
                        get_int(station.getElementsByTagName("bikesavailable")[0]),
                        get_int(station.getElementsByTagName("slotsavailable")[0]),
                        get_text(station.getElementsByTagName("name")[0]),
                        get_text(station.getElementsByTagName("district")[0]),
                        get_float(station.getElementsByTagName("longitude")[0]),
                        get_float(station.getElementsByTagName("latitude")[0]),
                        datetime.datetime.now()
                    )
                    self.session.add( new_bike_station )
                except:
                    print 'At least one tag misses: num, name, state, lat, lon, availableSlots, availableBikes, districtName'
        self.session.commit()


class BikeStationUpdater():
    def __init__(self, db_string):
        self.stations = []
        if not db_string:
            raise NameError('Database connection parameters are empty')
        self.engine = create_engine(db_string)
        self.metadata = MetaData(bind = self.engine)
        self.bike_stations_table = Table('bike_stations', self.metadata,
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
        mapper(BikeStation, self.bike_stations_table)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        for tmp in self.session.query( BikeStation ).all():
            #print tmp.district_name.encode("utf-8") + " : " + tmp.name.encode("utf-8") + " : " + tmp.chrone.strftime("%H:%M") + " : " + str(tmp.id_station)
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
                #print s
                self.stations.append(s)
            except:
                print 'At least one tag misses: num, name, lat, lon, availableSlots, availableBikes, districtName, chrone'
    def to_string(self):
        title = '<div id=\'bikes\'><span class=\'smallTitle\'>'
        textRed = '<span class=\'bikeRed\'>'
        textOrange = '<span class=\'bikeOrange\'>'
        tinyText = '<span class=\'tinyText\'>'
        res = 'lat\tlon\ttitle\tdescription\ticon\ticonSize\ticonOffset\n'
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

class BikeStation(object):
    def __init__(self, id_station, av_bikes, av_slots, name, district_name, lon, lat, chrone): 
        self.id_station = id_station
        self.av_bikes = av_bikes
        self.av_slots = av_slots
        self.name = name
        self.district_name = district_name
        self.lon = lon
        self.lat = lat
        self.chrone = chrone
   
    def __repr__(self):
        return "<BikeStation('%s','%s','%s','%s','%s','%s','%s','%s')>" % (self.id_station, self.av_bikes, self.av_slots, self.name,self.district_name, self.lon, self.lat, self.chrone)
        


if __name__ == "__main__":
    u = "http://data.keolis-rennes.com/xml/?version=1.0&key=UAYPAP0MHD482NR&cmd=getstation&param[request]=all"
    #v = BikeStationImporter( u, 'sqlite:////home/ody/bikes.db')
    v = BikeStationUpdater( 'sqlite:////home/ody/bikes.db' )
    print v.to_string()
    print "Done!"
