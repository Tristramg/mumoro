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

    def __init__(self):
        bikesDatabaseURL = 'http://data.keolis-rennes.com/xml/'
        bikesMumoroREAPIKey = 'UAYPAP0MHD482NR'
        url = bikesDatabaseURL + "?version=1.0&key=" + bikesMumoroREAPIKey + "&cmd=getstation&param[request]=all"
        xml = urllib.urlopen(url)
        
        doc = parse(xml)
        self.stations = []
    
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
        title = '<bikeTitle>'
        textRed = '<bikeTextRed>'
        textOrange = '<bikeTextOrange>'
        smallText = '<bikeSmallText>'

        res = 'lat\tlon\ttitle\tdescription\ticon\ticonSize\ticonOffset\n'
    
        for s in self.stations:
            res += '%f\t%f\t' % (s['lat'], s['lon'])
            res += (title + s['name'] + '<br>(' + s['num'] + ')</bikeTitle><br>\t')
            if (s['state'] == 0):
                res += ( textRed + 'Station supports only bike deposits</bikeTextRed><br>')
            elif (s['availableBikes'] == 0):
                res += ( textRed + 'No available bikes</bikeTextRed><br>')
            elif (s['availableBikes'] < 3):
                res += ( textOrange + 'Available bikes : %i </bikeTextOrange><br>' % s['availableBikes'])
            else:
                res += ( title + 'Available bikes : %i </bikeTitle><br>' % s['availableBikes'])

            if (s['availableSlots'] == 0):
                res += ( textRed + 'No available deposit slots</bikeTextRed><br>')
            elif (s['availableSlots'] < 3):
                res += ( textOrange + 'Available slots : %i </bikeTextOrange><br>' % s['availableSlots'])
            else:
                res += ( title + 'Available slots : %i  </bikeTitle><br>' % s['availableSlots'] )
            res += ('<br><br>' + smallText + 'Click again to close</bikeSmallText>\t')

            if (s['availableSlots'] == 0 or s['availableBikes'] == 0 or ['state'] == 0):
                res += ('img/bike.station.red.png\t18,18\t0,0\n')
            elif (s['availableSlots'] < 3 or s['availableBikes'] < 3):
                res += ('img/bike.station.orange.png\t18,18\t0,0\n')
            elif (s['availableSlots'] > 3 and s['availableBikes'] > 3):
                res += ('img/bike.station.green.png\t18,18\t0,0\n')
         
        return res


if __name__ == "__main__":

    v = VeloStar()
    print v.to_string()
