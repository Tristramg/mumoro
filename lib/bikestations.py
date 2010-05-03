import os.path
import urllib
from xml.dom.minidom import parse

def get_text(node):
    return node.childNodes[0].nodeValue

def get_int(node):
    return int(get_text(node))

def get_float(node):
    return float(get_text(node))

class VeloStar:
    stations = []
    def __init__(self):
        bikesDatabaseURL = 'http://data.keolis-rennes.com/xml/'
        bikesMumoroREAPIKey = 'UAYPAP0MHD482NR'
        url = bikesDatabaseURL + "?version=1.0&key=" + bikesMumoroREAPIKey + "&cmd=getstation&param[request]=all"
        xml = urllib.urlopen(url)
        
        doc = parse(xml)
    
            #self.__currentNode__ = self.doc.documentElement
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
                     'districtName': get_text(station.getElementsByTagName("district")[0])
                     }
                    self.stations.append(s)
                except:
                    print 'At least one tag misses: num, name, state, lat, lon, availableSlots, availableBikes, districtName'

    def to_string(self):
        title = '<div id=\'bikes\'><span class=\'smallTitle\'>'
        textRed = '<span class=\'bikeRed\'>'
        textOrange = '<span class=\'bikeOrange\'>'
        tinyText = '<span class=\'tinyText\'>'

        res = 'lat\tlon\ttitle\tdescription\ticon\ticonSize\ticonOffset\n'
    
        for s in self.stations:
            res += '%f\t%f\t' % (s['lat'], s['lon'])
            res += (title + s['name'] + '<br>(' + s['num'] + ')</span><br>\t')
            if (s['state'] == 0):
                res += ( textRed + 'Station supports only bike deposits</span><br>')
            elif (s['availableBikes'] == 0):
                res += ( textRed + 'No available bikes</span><br>')
            elif (s['availableBikes'] < 3):
                res += ( textOrange + '%i Available bikes</span><br>' % s['availableBikes'])
            else:
                res += ( title + '%i Available bikes</span><br>' % s['availableBikes'])

            if (s['availableSlots'] == 0):
                res += ( textRed + 'No available deposit slots</span><br>')
            elif (s['availableSlots'] < 3):
                res += ( textOrange + '%i Available slots</span><br>' % s['availableSlots'])
            else:
                res += ( title + '%i Available slots</span><br>' % s['availableSlots'] )
            res += ('<br><br>' + tinyText + 'Click again to close</span></div>\t')

            if (s['availableSlots'] == 0 or s['availableBikes'] == 0 or ['state'] == 0):
                res += ('img/bike.station.red.png\t18,25\t-8,-25\n')
            elif (s['availableSlots'] < 3 or s['availableBikes'] < 3):
                res += ('img/bike.station.orange.png\t18,25\t-8,-25\n')
            elif (s['availableSlots'] > 3 and s['availableBikes'] > 3):
                res += ('img/bike.station.green.png\t18,25\t-8,-25\n')
        return res


if __name__ == "__main__":

    v = VeloStar()
    print v.to_string()
