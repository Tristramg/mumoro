import bikestations
import psycopg2 as pg

class StationsBikesInfo:
    conn = None
    def __init__(self):
	self.addData()
    def createTable(self):
	pass
    def addData(self):
	s = bikestations.VeloStar()
        try:
            tmp = "dbname=guidage user=guidage"
            self.conn = pg.connect( tmp )
        except:
            print "I am unable to connect to the database"
        cur = self.conn.cursor()
        query = "TRUNCATE TABLE bike_stations_info"
	try:        
	    cur.execute( query )
	except Exception as ex:
            print "I am unable to empty data from the database"
            print ex
        self.conn.commit()
        for i in s.stations:
            self.addStationInfoData(i)
        self.conn.close()
    def addStationInfoData(self,s):
	cur = self.conn.cursor()
        query = "INSERT INTO bike_stations_info (\"id_station\", \"name\", \"district_name\", \"lon\", \"lat\") VALUES (%s, %s, %s, %s, %s)"
	try:        
	    cur.execute( query , [ s['num'], s['name'], s['districtName'], s['lon'], s['lat'] ] )
	except Exception as ex:
            print "I am unable to insert data into the database"
            print ex
        self.conn.commit()
        
if __name__ == "__main__":
    x=StationsBikesInfo()
        
