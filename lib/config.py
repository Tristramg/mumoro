import ConfigParser
import string
import os.path

class Config:
    host = ""
    dbname = ""
    dbuser = ""
    dbpassword = ""
    tableNodes = ""
    tableEdges = ""
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
		if( self.dbname == "" or self.dbuser == "" or self.host == "" or self.tableNodes == "" or self.tableEdges == "" ):
			print "Error reading configuration file. Check values in config.cfg"
		else:
			print "Configuration loaded successfully"
