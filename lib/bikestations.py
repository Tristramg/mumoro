import os.path



from struct import unpack

class Station:
    num = None
    name = None
    state = None
    lat = None
    lon = None
    availableSlots = None
    availableBikes = None
    districtName = None
    def __init__(self):
        pass
class TransformXmlToBikesStations:
    __currentNode__ = None
    __stationsList__ = None
    def __init__(self):
        self.readXml()
    def readXml(self):
        from xml.dom.minidom import parse
        self.doc = parse('bike.stations.xml')
    def getRootElement(self):
        if self.__currentNode__ == None:
            self.__currentNode__ = self.doc.documentElement
        return self.__currentNode__
    def getStations(self):
        if self.__stationsList__ != None:
            return
        self.__stationsList__ = []

        for stations in self.getRootElement().getElementsByTagName("station"):
            if stations.nodeType == stations.ELEMENT_NODE:
                s = Station()
                try:
                    s.num = self.getText(stations.getElementsByTagName("id")[0])
		    s.name = self.getText(stations.getElementsByTagName("name")[0])
		    s.state = self.getText(stations.getElementsByTagName("state")[0])
		    s.lat = self.getText(stations.getElementsByTagName("latitude")[0])
		    s.lon = self.getText(stations.getElementsByTagName("longitude")[0])
		    s.availableSlots = self.getText(stations.getElementsByTagName("slotsavailable")[0])
		    s.availableBikes = self.getText(stations.getElementsByTagName("bikesavailable")[0])
		    s.districtName = self.getText(stations.getElementsByTagName("district")[0])
                except:
                    print 'At least one tag misses: num, name, state, lat, lon, availableSlots, availableBikes, districtName'
                self.__stationsList__.append(s)
        return self.__stationsList__
    def getText(self, node):
        return node.childNodes[0].nodeValue

class TxtStationGenerator:
    title = '<bikeTitle>'
    textRed = '<bikeTextRed>'
    textOrange = '<bikeTextOrange>'
    smallText = '<bikeSmallText>'
    def __init__(self):
        pass
    def toString(self):
        return ('lat\tlon\ttitle\tdescription\ticon\ticonSize\ticonOffset\n')
    def toStringStation(self,s):
	res = (s.lat + '\t' + s.lon + '\t')
        res += (self.title + s.name + '<br>(' + s.num + ')</bikeTitle><br>\t')
        if (int(s.state) == 0):
            res += ( self.textRed + 'Station supports only bike deposits</bikeTextRed><br>')
        elif (int(s.availableBikes) == 0):
            res += ( self.textRed + 'No available bikes</bikeTextRed><br>')
        elif (int(s.availableBikes) < 3):
            res += ( self.textOrange + 'Available bikes : ' + s.availableBikes + '</bikeTextOrange><br>')
        else:
            res += ( self.title + 'Available bikes : ' + s.availableBikes + '</bikeTitle><br>')
        if (int(s.availableSlots) == 0):
            res += ( self.textRed + 'No available deposit slots</bikeTextRed><br>')
        elif (int(s.availableSlots) < 3):
            res += ( self.textOrange + 'Available slots : ' + s.availableSlots + '</bikeTextOrange><br>')
        else:
            res += ( self.title + 'Available slots : ' + s.availableSlots + '</bikeTitle><br>')
        res += ('<br><br>' + self.smallText + 'Click again to close</bikeSmallText>\t')
        if (int(s.availableSlots) == 0 or int(s.availableBikes) == 0 or int(s.state) == 0):
             res += ('img/bike.station.red.png\t18,18\t0,0\n')
        elif (int(s.availableSlots) < 3 or int(s.availableBikes) < 3):
             res += ('img/bike.station.orange.png\t18,18\t0,0\n')
        elif (int(s.availableSlots) > 3 and int(s.availableBikes) > 3):
             res += ('img/bike.station.green.png\t18,18\t0,0\n')
        return res

