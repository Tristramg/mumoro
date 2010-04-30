import bikestations
import psycopg2 as pg
import time
import config

class StatsBikes:
    conn = None
    def __init__(self):
	self.addData()
    def createTable(self):
	pass
    def addData(self):
	c = config.Config()	
	s = bikestations.VeloStar()
        try:
            if( c.host != "" ):
                tmp = ("dbname=%s user=%s password=%s host=%s") % ( c.dbname, c.dbuser, c.dbpassword, c.host )
                self.conn = pg.connect( tmp )
            else:
                tmp = ("dbname=%s user=%s password=%s") % ( c.dbname, c.dbuser, c.dbpassword )
                self.conn = pg.connect( tmp )
        except:
            print "I am unable to connect to the database"
        for i in s.stations:
            self.addStationData(i)
        self.conn.close()
    def addStationData(self,s):
	c = config.Config()        
	cur = self.conn.cursor()
        day = time.gmtime(time.time())[6]
        chrone = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        query = "INSERT INTO " + c.tableBikeStats +" (\"idDay\", \"idStation\", \"avSlots\", \"avBikes\", \"chrone\") VALUES (%s, %s, %s, %s, %s)"
	try:        
	    cur.execute( query , [ day, s['num'], s['availableSlots'], s['availableBikes'], chrone ] )
	except Exception as ex:
            print "I am unable to insert data into the database"
            print ex
        self.conn.commit()
        
if __name__ == "__main__":
    x=StatsBikes()
        
