import ConfigParser
import string
import os.path
import locale

class Config:
    host = ""
    dbname = ""
    dbuser = ""
    dbpassword = ""
    tableNodes = ""
    tableEdges = ""
    tableURL = ""
    tableBikeStations = ""
    urlHash = ""
    cpPort = 0
    def __init__(self):
	if not os.path.exists("config.cfg"):        
		print "No configuration file found !"
	else:		
		config = ConfigParser.ConfigParser()
        	config.read("config.cfg")
        	self.dbname = config.get("DBSettings","DBName");
        	self.dbuser = config.get("DBSettings","DBUser");
        	self.dbpassword = config.get("DBSettings","DBPassword");
        	self.host = config.get("DBSettings","DBHost");
        	self.tableNodes = config.get("DBSettings","DBTableNodes");
        	self.tableEdges = config.get("DBSettings","DBTableEdges");
                self.tableURL = config.get("DBSettings","DBTableURL");
                self.tableBikeStations = config.get("DBSettings","DBTableBikeStationsInfo");
                self.urlHash = config.get("DBSettings","URLHash");
                self.cpPort = locale.atoi( config.get("DBSettings","CherrypyPort") );
		
