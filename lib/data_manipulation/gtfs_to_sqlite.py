import sqlite3
import sys
import transitfeed
import datetime
from optparse import OptionParser

def convert(gtfs, sqlite, network_name, start_date, end_date):
    s = transitfeed.Schedule()
    s.Load(gtfs)
    sql = sqlite3.connect(sqlite)
    sql.executescript('''CREATE TABLE IF NOT EXISTS nodes(
                    id INTEGER PRIMARY KEY,
                    original_id TEXT,
                    lon REAL,
                    lat REAL,
                    network TEXT,
                    route TEXT
                );
                CREATE INDEX IF NOT EXISTS lon_lat_idx ON nodes(lon, lat);
                CREATE INDEX IF NOT EXISTS id_idx ON nodes(id);
                CREATE INDEX IF NOT EXISTS id_idx ON nodes(original_id);

                CREATE TABLE IF NOT EXISTS edges (
                    id INTEGER PRIMARY KEY,
                    source INTEGER,
                    target INTEGER,
                    start_secs INTEGER,
                    arrival_secs INTEGER,
                    services TEXT
                 );
    ''')

    #Start with mapping (route_id, stop_id) to an int
    map = {}
    c = sql.cursor()
    c.execute("SELECT MAX(id) from nodes")
    row = c.fetchone()
    if (row != None and row[0] != None):
        count = int(row[0]) + 1
    else:
        count = 0
    query_nodes = "INSERT INTO nodes (id, original_id, lon, lat, network, route) VALUES(?, ?, ?, ?, ?, ?)"
    query_edges = "INSERT INTO edges (source, target, start_secs, arrival_secs, services) VALUES(?, ?, ?, ?, ?)" 
    for trip in s.GetTripList():
        service_period = s.GetServicePeriod(trip.service_id)
        services = ""
        delta = datetime.timedelta(days=1)
        date = start_date
        while date <= end_date:
            if service_period.IsActiveOn(date.strftime("%Y%m%d"), date_object=date):
                services = "1" + services
            else:
                services = "0" + services
            date += delta
            
        if not map.has_key(trip.route_id):
            map[trip.route_id] = {}
        prev_time = None
        prev_stop = None
        current_stop = None
        for stop in trip.GetStopTimes():
            if not map[trip.route_id].has_key(stop.stop_id):
                map[trip.route_id][stop.stop_id] = count
                sql.execute(query_nodes, (count, stop.stop_id, stop.stop.stop_lon, stop.stop.stop_lat, network_name, trip.route_id))
                count +=1
            current_stop = map[trip.route_id][stop.stop_id]
            if prev_stop != None:
                sql.execute(query_edges, (prev_stop, current_stop, prev_time, stop.arrival_secs, services))
            prev_stop = current_stop
            prev_time = stop.departure_secs

    sql.commit()


if __name__ == '__main__':
    parser = OptionParser("Usage: %prog gtfs_file.zip database_name network_name start_date end_date")
    (options, args) = parser.parse_args()
    if len(args) != 5:
        sys.stderr.write("Wrong number of arguments. Expected 5, got {0}\n".format(len(args)))
        sys.exit(1)

    start = datetime.datetime.strptime(args[3], "%Y%m%d")
    end = datetime.datetime.strptime(args[4], "%Y%m%d")

    convert(args[0], args[1], args[2], start, end)
