import updatebikesstations
import bikestations
import psycopg2 as pg
import time

class StatsBikes:
    host = ''
    dbname = ''
    user = ''
    password = ''
    conn = None
    def __init__(self,db,ho,us,pa):
	self.host = ho
	self.dbname = db
	self.user = us
	self.password = pa
        pass
    def createTable(self):
	pass
    def addData(self):
	updatebikes = updatebikesstations.UpdateBikesStations()
        updatebikes.updateXmlBikes()
        pars = bikestations.TransformXmlToBikesStations()
        stationList = pars.getStations()
        try:
            tmp = ("dbname=%s user=%s password=%s host=%s") % ( self.dbname, self.user, self.password, self.host )
            self.conn = pg.connect( tmp );
        except:
            print "I am unable to connect to the database"
        for s in stationList:
            self.addStationData(s)
        self.conn.commit()
        self.conn.close()
    def addStationData(self,s):
        cur = self.conn.cursor()
        day = time.gmtime(time.time())[6]
        chrone = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        query = "INSERT INTO bike_stats(\"idDay\", \"idStation\", \"avSlots\", \"avBikes\", \"chrone\") VALUES (%s, %s, %s, %s, %s)"
	try:        
	    cur.execute( query , [ day, s.num, s.availableSlots, s.availableBikes, chrone ] )
	except Exception as ex:
            print "I am unable to insert data into the database"
            print ex

if __name__ == "__main__":
    x=StatsBikes('mumoroRE','localhost','root','takis')
    x.addData()
        
