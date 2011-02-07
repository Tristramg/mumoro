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
#    © Université Toulouse 1 Capitole 2010
#    © Tristram Gräbener 2011
#    Author: Tristram Gräbener

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
    count = 1
    routes_count = 1
    routes_map = {}

    for route in s.GetRouteList():
        session.add(PT_Line(route.route_id, route.route_short_name, route.route_long_name, route.route_color, route.route_text_color, route.route_desc))
        routes_map[route.route_id] = routes_count
        routes_count += 1

    stop_areas_count = 1
    stop_areas_map = {}
    for stop in s.GetStopList():
        if stop.parent_station == '':
            session.add(PT_StopArea(stop.stop_id, stop.stop_name))
            stop_areas_map[stop.stop_id] = stop_areas_count
            stop_areas_count += 1

    for trip in s.GetTripList():
        route =  s.GetRoute(trip.route_id)
        mode = route.route_type
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
                session.add(PT_Node(stop.stop_id, stop.stop.stop_lon, stop.stop.stop_lat, trip.route_id, stop_areas_map[stop.stop_id]))
                count +=1
            current_stop = map[trip.route_id][stop.stop_id]
            current_node = session.query(PT_Node).filter_by(original_id = stop.stop_id).first()
            if prev_stop != None:
                length = distance( (current_node.lon, current_node.lat), (prev_node.lon, prev_node.lat))
                session.add(PT_Edge(prev_stop, current_stop, length * 1.1, prev_time, stop.arrival_secs, service, mode, routes_map[route.route_id]))

            prev_node = current_node 
            prev_stop = current_stop
            prev_time = stop.departure_secs

            if count % 1000 == 0:
                session.flush()
            if count % 10000 == 0:
                print "Added {0} timetable elements".format(self.count)

    for k, v in services_map.items():
        session.add(PT_Service(v, k))
    session.commit()


