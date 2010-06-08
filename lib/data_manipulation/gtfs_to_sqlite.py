import sqlite3
import transitfeed

def convert(gtfs, sqlite, network_name):
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
                    arrival_secs INTEGER
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
    query_edges = "INSERT INTO edges (source, target, start_secs, arrival_secs) VALUES(?, ?, ?, ?)" 
    for trip in s.GetTripList():
        if s.GetServicePeriod(trip.service_id).IsActiveOn("20100430"):
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
                    sql.execute(query_edges, (prev_stop, current_stop, prev_time, stop.arrival_secs))
                prev_stop = current_stop
                prev_time = stop.departure_secs


    sql.commit()

#convert('bart.zip', 'pt2', 'bart')
convert('la.zip', 'la', 'metro')
