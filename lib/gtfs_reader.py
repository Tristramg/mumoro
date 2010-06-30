from datastructures import *
import sys
import transitfeed
import datetime
from optparse import OptionParser

def convert(filename, nodes_table, edges_table, start_date, end_date):
    s = transitfeed.Schedule()
    s.Load(gtfs)
    
    

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


