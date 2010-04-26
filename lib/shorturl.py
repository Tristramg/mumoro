import hashlib
import string
import config
import psycopg2 as pg
import simplejson as json

class shortURL:
    conn = None
    def __init__(self):
        pass

    def addRouteToDatabase(self,lonMap,latMap,zoom,lonStart,latStart,lonDest,latDest,addressStart,addressDest):
        c = config.Config()
        try:
            tmp = ("dbname=%s user=%s password=%s host=%s") % ( c.dbname, c.dbuser, c.dbpassword, c.host )
            self.conn = pg.connect( tmp );
        except:
            print "I am unable to connect to the database"
        h = hashlib.md5()
        h.update(addressStart)
        h.update(addressStart)
        h.update(str(lonStart))
        h.update(str(latStart))
        h.update(str(lonDest))
        h.update(str(latDest))
        h.update(str(lonMap))
        h.update(str(latMap))
        h.update(str(zoom))
        cur = self.conn.cursor()
        query = "INSERT INTO " + c.tableURL + "(\"id\", \"zoom\", \"lonMap\", \"latMap\", \"lonStart\", \"latStart\", \"lonDest\", \"latDest\", \"addressStart\", \"addressDest\") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
	try:        
	    cur.execute( query , [ h.hexdigest()[0:16], zoom, lonMap, latMap, lonStart, latStart, lonDest, latDest, addressStart, addressDest ] )
	except Exception as ex:
            print "I am unable to insert data into the database"
            print ex
        self.conn.commit()
        self.conn.close()

    def hashExists(self,value):
	res = False        
	c = config.Config()
        try:
            tmp = ("dbname=%s user=%s password=%s host=%s") % ( c.dbname, c.dbuser, c.dbpassword, c.host )
            self.conn = pg.connect( tmp );
        except:
            print "I am unable to connect to the database"
        cur = self.conn.cursor()
        query = ("SELECT COUNT(*) as nb FROM %s WHERE id='%s'") % ( c.tableURL, value) 
	try:        
	    cur.execute( query )
	except Exception as ex:
            print "I am unable to verify if hash exists in the database"
            print ex
        if( int(cur.fetchone()[0]) == 0 ):
            res = False
        else:
            res = True
        self.conn.close()
        return res

    def getDataFromHash(self,value):
        if( not self.hashExists(value) ):
            print ("Route %s NOT found!") % (value)
        else:
            c = config.Config()
            try:
                tmp = ("dbname=%s user=%s password=%s host=%s") % ( c.dbname, c.dbuser, c.dbpassword, c.host )
                self.conn = pg.connect( tmp );
            except:
                print "I am unable to connect to the database reee"
            cur = self.conn.cursor()
            query = ("SELECT * FROM %s WHERE id='%s'") % ( c.tableURL, value) 
	    try:        
	        cur.execute( query )
	    except Exception as ex:
                print "I am unable to read data from the database"
                print ex
            tmp = cur.fetchone()
            res = {
                    'zoom': tmp[1],
                    'lonMap': tmp[2],
                    'latMap' : tmp[3],
                    'lonStart': tmp[4],
                    'latStart': tmp[5],
                    'lonDest' : tmp[6],
                    'latDest' : tmp[7],
                    'addressStart': tmp[8],
                    'addressDest': tmp[9]
            }
            #print res
            self.conn.close()
            return "test"
            #return json.dumps(res)

