import urllib
import bikestations

class UpdateBikesStations:
    bikesDatabaseURL = 'http://data.keolis-rennes.com/xml/'
    bikesMumoroREAPIKey = 'UAYPAP0MHD482NR'
    def __init__(self):
        pass
    def updateXmlBikes(self):
	#update description and status for all bike stations. No filer is applied on the query
	#save the response in bikes.stations.xml
	fileXml = "bike.stations.xml"
	print "Updating bike stations status into xml file : %s" %fileXml
	url= self.bikesDatabaseURL + "?version=1.0&key=" + self.bikesMumoroREAPIKey + "&cmd=getstation&param[request]=all"	
	urllib.urlretrieve(url, fileXml)
	print "     Done!"
    def xmlToString(self):
        pars = bikestations.TransformXmlToBikesStations()
        stationList = pars.getStations()
        streamControl = bikestations.TxtStationGenerator()
        res =streamControl.toString()
        for s in stationList:
            res += streamControl.toStringStation(s)
        return res
