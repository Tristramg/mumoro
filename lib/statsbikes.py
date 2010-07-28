# -*- coding: utf-8 -*-

#    This file is part of Mumoro.
#
#    Mumoro is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Mumoro is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Mumoro.  If not, see <http://www.gnu.org/licenses/>.
#
#    © Université de Toulouse 1 2010
#    Author: Tristram Gräbener, Odysseas Gabrielides

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
        
