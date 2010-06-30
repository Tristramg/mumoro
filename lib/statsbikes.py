import bikestations
import psycopg2 as pg
import time

class StatsBikes:
    conn = None
    def __init__(self):
	self.addData()
    def createTable(self):
	pass
    def addData(self):
	s = bikestations.VeloStar(False)
        try:
            tmp = "dbname=guidage user=guidage"
            self.conn = pg.connect( tmp )
        except:
            print "I am unable to connect to the database"
        cur = self.conn.cursor()
        query = "TRUNCATE TABLE bike_stations"
	try:        
	    cur.execute( query )
	except Exception as ex:
            print "I am unable to empty data from the database"
            print ex
        for i in s.stations:
            self.addStationData(i)
        self.conn.commit()
        self.conn.close()
    def addStationData(self,s):
	cur = self.conn.cursor()
        day = time.localtime(time.time())[6]
        chrone = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        query = "INSERT INTO bike_stats (\"idDay\", \"idStation\", \"avSlots\", \"avBikes\", \"chrone\") VALUES (%s, %s, %s, %s, %s)"
	try:        
	    cur.execute( query , [ day, s['num'], s['availableSlots'], s['availableBikes'], chrone ] )
	except Exception as ex:
            print "I am unable to insert bike stations stats data into the database"
            print ex
        query = "INSERT INTO bike_stations (\"id_station\", \"av_bikes\", \"av_slots\", \"name\", \"district_name\", \"lon\", \"lat\", \"chrone\") VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
	try:        
	    cur.execute( query , [ s['num'], s['availableBikes'], s['availableSlots'], s['name'], s['districtName'], s['lon'], s['lat'], chrone ] )
	except Exception as ex:
            print "I am unable to insert bike stations stats data into the database"
            print ex
if __name__ == "__main__":
    x=StatsBikes()
        
