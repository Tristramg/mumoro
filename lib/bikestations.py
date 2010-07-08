import os.path
import urllib
from xml.dom.minidom import parse
import datetime
import time

from sqlalchemy import *
from sqlalchemy.orm import *

def get_text(node):
    return node.childNodes[0].nodeValue

def get_int(node):
    return int(get_text(node))

def get_float(node):
    return float(get_text(node))

class VeloStar:
    def __init__(self,fromDB, metadata):
        self.stations = []

        self.bike_stations_table = Table('bike_stations', metadata,
        Column('id_station', Integer, primary_key=True),
        Column('av_bikes', Integer),
        Column('av_slots', Integer),
        Column('name', Text),
        Column('district_name', Text),
        Column('lon', Float),
        Column('lat', Float),
        Column('chrone', DateTime(timezone=False)),
        )
        metadata.create_all()
        if( fromDB ):
            self.from_db()
        else:
            self.from_xml()
    
    def from_xml(self):
        bikesDatabaseURL = 'http://data.keolis-rennes.com/xml/'
        bikesMumoroREAPIKey = 'UAYPAP0MHD482NR'
        url = bikesDatabaseURL + "?version=1.0&key=" + bikesMumoroREAPIKey + "&cmd=getstation&param[request]=all"
        xml = urllib.urlopen(url)
        doc = parse(xml)
        for station in doc.documentElement.getElementsByTagName("station"):
            if station.nodeType == station.ELEMENT_NODE:
                try:
                    s = {
                     'num': get_text(station.getElementsByTagName("id")[0]),
                     'name': get_text(station.getElementsByTagName("name")[0]),
                     'state': get_int(station.getElementsByTagName("state")[0]),
                     'lat': get_float(station.getElementsByTagName("latitude")[0]),
                     'lon': get_float(station.getElementsByTagName("longitude")[0]),
                     'availableSlots': get_int(station.getElementsByTagName("slotsavailable")[0]),
                     'availableBikes': get_int(station.getElementsByTagName("bikesavailable")[0]),
                     'districtName': get_text(station.getElementsByTagName("district")[0]),
		     'chrone': time.strftime("%H:%M", time.localtime())
                     }
                    self.stations.append(s)
                except:
                    print 'At least one tag misses: num, name, state, lat, lon, availableSlots, availableBikes, districtName'
    def from_db(self):
        for tmp in self.bike_stations_table.select().execute():
            try:
                s = {
                 'num': str(tmp.id_sation),
                 'name': tmp.name,
                 'state': "1",
                 'lat': tmp.lat,
                 'lon': tmp.lon,
                 'availableSlots': tmp.av_bikes,
                 'availableBikes': tmp.av_slots,
                 'districtName': tmp.district_name,
                 'chrone': tmp.chrone.strftime("%H:%M")
                }
                self.stations.append(s)
            except:
                print 'At least one tag misses: num, name, lat, lon, availableSlots, availableBikes, districtName'
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
            return "<hurl('%s','%s','%s','%s','%s','%s','%s','%s')>" % (self.id_station, self.av_bikes, self.av_slots, self.name,self.district_name, self.lon, self.lat, self.chrone)


if __name__ == "__main__":

    v = VeloStar(True)
    print v.to_string()
