from datastructures import *
import sys
import transitfeed
import datetime
from optparse import OptionParser
from sqlalchemy.orm import mapper, sessionmaker

def distance(c1, c2):
    try:
        delta = c2[0] - c1[0]
        a = math.radians(c1[1])
        b = math.radians(c2[1])
        C = math.radians(delta)
        x = math.sin(a) * math.sin(b) + math.cos(a) * math.cos(b) * math.cos(C)
        distance = math.acos(x) # in radians
        distance  = math.degrees(distance) # in degrees
        distance  = distance * 60 # 60 nautical miles / lat degree
        distance = distance * 1852 # conversion to meters
        return distance;
    except:
        return 0


def convert(filename, session, start_date, end_date):
    map = {}
    services_map = {}
    s = transitfeed.Schedule()
    s.Load(filename)
    
    start_date = datetime.datetime.strptime(start_date, "%Y%m%d")
    end_date = datetime.datetime.strptime(end_date, "%Y%m%d")
    

    #Start with mapping (route_id, stop_id) to an int
    count = 0

    for trip in s.GetTripList():
        mode = s.GetRoute(trip.route_id).route_type
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
            
        if not services_map.has_key(services):
            services_map[services] = len(services_map)
        service = services_map[services]

        if not map.has_key(trip.route_id):
            map[trip.route_id] = {}
        prev_time = None
        prev_stop = None
        current_stop = None
        for stop in trip.GetStopTimes():
            if not map[trip.route_id].has_key(stop.stop_id):
                map[trip.route_id][stop.stop_id] = count
                session.add(PT_Node(stop.stop_id, stop.stop.stop_lon, stop.stop.stop_lat, trip.route_id))
                count +=1
            current_stop = map[trip.route_id][stop.stop_id]
            current_node = session.query(PT_Node).filter_by(original_id = stop.stop_id).first()
            if prev_stop != None:
                length = distance( (current_node.lon, current_node.lat), (prev_node.lon, prev_node.lat))
                session.add(PT_Edge(prev_stop, current_stop, length * 1.1, prev_time, stop.arrival_secs, service, mode))

            prev_node = current_node 
            prev_stop = current_stop
            prev_time = stop.departure_secs

            if count % 1000 == 0:
                self.session.flush()
            if count % 10000 == 0:
                print "Added {0} timetable elements".format(self.count)

    for k, v in services_map.items():
        session.add(PT_Service(v, k))
    session.commit()


