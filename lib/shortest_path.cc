/*
    This file is part of Mumoro.

    Mumoro is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Mumoro is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Mumoro.  If not, see <http://www.gnu.org/licenses/>.
*/

#include "graph.h"
#include "shortest_path.h"
#include "boost/date_time/gregorian/gregorian_types.hpp"
#include "boost/date_time/gregorian/gregorian.hpp" //include all types plus i/o
#include "sqlite3.h"
using namespace boost;
using namespace boost::posix_time;
using namespace boost::gregorian;


namespace Mumoro
{
    struct compare
    {
        bool operator()(const double & a, const double & b) const
        {
            return a < b;
        }

        bool operator()(const FunctionPtr &, const double &) const
        {
            return false;
        }
    };

    Const_cost::Const_cost(double cost) : m_cost(cost) {}

    double Const_cost::operator()(double in) const
    {
        return in + m_cost;
    }

    Velouse_cost::Velouse_cost(time_duration opening, time_duration closing, double cost):
        m_opening(opening), m_open_duration(closing), m_cost(cost)
    {
        //       assert(closing < opening);
    }

    double Velouse_cost::operator()(double in) const
    {
        ptime current = from_time_t( (time_t) in);
        date today = current.date();
        date yesterday = today - days(1);
        time_period today_opening(ptime(today, m_opening), m_open_duration);
        time_period yesterday_opening(ptime(yesterday, m_opening), m_open_duration);

        if ( today_opening.contains(current) || yesterday_opening.contains(current) )
            return in + m_cost;
        else
            return in + m_cost + (today_opening.end() - current).total_seconds();
    }

    struct Combine_distance
    {
        double operator()(double time_so_far, FunctionPtr f) const
        {
            return (*f)(time_so_far);
        }
    };

    struct found_goal
    {
    }; // exception for termination

    // visitor that terminates when we find the goal

    class dijkstra_goal_visitor : public boost::default_dijkstra_visitor
    {
        public:

            dijkstra_goal_visitor(cvertex goal) : m_goal(goal)
        {
        }

            template<class CGraph>
                void examine_vertex(cvertex u, CGraph& g)
                {
                    if (u == m_goal)
                        throw found_goal();
                }
        private:
            cvertex m_goal;
    };

    bool Edge_property::operator<(Edge_property e) const
    {
        if (first < e.first)
            return true;
        else if (first == e.first && second < e.second)
            return true;
        else
            return false;
    }

    bool add_direct(sqlite3_stmt * stmt, Transport_mode m)
    {
        switch(m)
        {
            case Car: return (sqlite3_column_int(stmt, 6) != 0); break;
            case Bike: return (sqlite3_column_int(stmt,4) != 0); break;
            case Foot: return (sqlite3_column_int(stmt,3) != 0); break;
            case Subway: return (sqlite3_column_int(stmt,8) != 0); break;
            default: return false;
        }
    }

    bool add_reverse(sqlite3_stmt * stmt, Transport_mode m)
    {
        switch(m)
        {
            case Car: return (sqlite3_column_int(stmt, 7) != 0); break;
            case Bike: return (sqlite3_column_int(stmt,5) != 0); break;
            case Foot: return (sqlite3_column_int(stmt,4) != 0); break;
            case Subway: return (sqlite3_column_int(stmt,8) != 0); break;
            default: return false;
        }
    }

    FunctionPtr direct_cost(sqlite3_stmt * stmt, Transport_mode m)
    {
        double length = sqlite3_column_double(stmt, 2);
        switch(m)
        {
            case Car: return FunctionPtr( new Const_cost(length / car_speed) ); break;
            case Bike: return FunctionPtr( new Const_cost(length / bike_speed) ); break;
            case Foot: return FunctionPtr( new Const_cost(length / foot_speed) ); break;
            case Subway: return FunctionPtr( new Const_cost(length / subway_speed) ); break;
            default: return FunctionPtr( new Const_cost(INFINITY) ); 
        }
    }

    FunctionPtr reverse_cost(sqlite3_stmt * stmt, Transport_mode m)
    {
        return direct_cost(stmt, m);
    }


    int Shortest_path::node_internal_id_or_add(uint64_t node_id, std::map<uint64_t, int> & m)
    {
        std::map<uint64_t, int>::const_iterator it = m.find(node_id);
        if (it == m.end())
        {
            m[node_id] = node_count++;
            return (node_count - 1);
        }
        else
        {
            return (*it).second;
        }
    }

    int Shortest_path::node_internal_id_or_add( uint64_t node_id)
    {
        return node_internal_id_or_add(node_id, foot_map);
    }

    int Shortest_path::node_internal_id(uint64_t node_id)
    {
        std::map<uint64_t, int>::const_iterator it = foot_map.find(node_id);
        if (it == foot_map.end())
        {
            std::cerr << "Node not found: " << node_id << std::endl;
            throw Node_not_found();
        }
        else
            return (*it).second;
    }

    void Shortest_path::init(const char * db_file, Transport_mode m)
    {
 
        sqlite3_open(db_file, &db);
        std::string q="SELECT id, lon, lat FROM tmp_nodes WHERE lon > ? AND lon < ?  AND lat > ? AND lat < ?  ORDER BY abs(lon - ?) + abs(lat - ?)";
        sqlite3_prepare_v2(db, q.c_str(), -1, &match_stmt, NULL);

        std::string q2="SELECT id, lon, lat FROM tmp_nodes2 WHERE lon > ? AND lon < ?  AND lat > ? AND lat < ?  ORDER BY abs(lon - ?) + abs(lat - ?)";
        sqlite3_prepare_v2(db, q2.c_str(), -1, &match_stmt2, NULL);
        node_count = 0;
        sqlite3_stmt * stmt;

        sqlite3_prepare_v2(db, "select source, target, length, foot, bike, bike_r, car, car_r, subway from links", -1, &stmt, NULL);

        std::vector<Edge_property> edge_prop;
        Edge_property prop;

        std::back_insert_iterator<std::vector<Edge_property> > ii(edge_prop);

        while(sqlite3_step(stmt) == SQLITE_ROW)
        {
            if( add_direct(stmt, m) )
            {
double length = sqlite3_column_double(stmt,2);
            int source = node_internal_id_or_add(sqlite3_column_int64(stmt, 0)); 
            int target = node_internal_id_or_add(sqlite3_column_int64(stmt, 1)); 


                prop.length = length;
                prop.cost = direct_cost(stmt, m);
                prop.first = source;
                prop.second = target;
                prop.mode = m;
                *ii++ = prop;
            }

            if( add_reverse(stmt, m) )
            {
                double length = sqlite3_column_double(stmt,2);
            int source = node_internal_id_or_add(sqlite3_column_int64(stmt, 0)); 
            int target = node_internal_id_or_add(sqlite3_column_int64(stmt, 1)); 

               prop.length = length;
                prop.cost = reverse_cost(stmt, m);
                prop.first = target;
                prop.second = source;
                prop.mode = m;
                *ii++ = prop;
            }
        }

        std::cout << "Read the first layer" << std::endl;

        sqlite3_prepare_v2(db, "SELECT lon, lat from nodes WHERE id=?",
                -1, &get_node_stmt, NULL);


        sqlite3_exec(db, "DROP TABLE tmp_nodes", NULL, NULL, NULL);
        sqlite3_exec(db, "CREATE TABLE tmp_nodes(id int, lon double, lat double)", NULL, NULL, NULL);
        sqlite3_exec(db, "CREATE INDEX ON tmp_nodes(lon, lat)", NULL, NULL, NULL);
        sqlite3_prepare_v2(db, "INSERT INTO tmp_nodes (id, lon, lat) VALUES (?, ?, ?)", -1, &insert_match, NULL);

        sqlite3_exec(db, "DROP TABLE tmp_nodes2", NULL, NULL, NULL);
        sqlite3_exec(db, "CREATE TABLE tmp_nodes2(id int, lon double, lat double)", NULL, NULL, NULL);
        sqlite3_exec(db, "CREATE INDEX ON tmp_nodes2(lon, lat)", NULL, NULL, NULL);
        sqlite3_prepare_v2(db, "INSERT INTO tmp_nodes2 (id, lon, lat) VALUES (?, ?, ?)", -1, &insert_match2, NULL);
       
       
        std::map<uint64_t, int>::const_iterator mi;
        for( mi = foot_map.begin(); mi != foot_map.end(); mi++ )
        {
            sqlite3_reset(get_node_stmt);
            sqlite3_bind_int64(get_node_stmt, 1, (*mi).first);
            if(sqlite3_step(get_node_stmt) != SQLITE_ROW)
            {
                std::cerr << "Unable to get a node "
                    << "Error " << sqlite3_errcode(db) << ": " << sqlite3_errmsg(db) << std::endl;
                exit(EXIT_FAILURE);
            };
            float lon = sqlite3_column_double(get_node_stmt, 0);
            float lat = sqlite3_column_double(get_node_stmt, 1);

            sqlite3_reset(insert_match);
            sqlite3_bind_int64(insert_match, 1, (*mi).second);
            sqlite3_bind_double(insert_match, 2, lon);
            sqlite3_bind_double(insert_match, 3, lat);

            if(sqlite3_step(insert_match) != SQLITE_DONE)
            {
                std::cerr << "Unable to insert a node "
                    << "Error " << sqlite3_errcode(db) << ": " << sqlite3_errmsg(db) << std::endl;
                exit(EXIT_FAILURE);
            };
        }

        std::cout << "Added nodes for a future map match" << std::endl;


        
        std::map<uint64_t, int> tmp_map;
        int offset = node_count;
        node_count = 0;
        sqlite3_prepare_v2(db, "select source, target, length, foot, bike, bike_r, car, car_r, subway from links", -1, &stmt, NULL);
        while(sqlite3_step(stmt) == SQLITE_ROW)
        {
           if( add_direct(stmt, Subway) )
            {
             double length = sqlite3_column_double(stmt,2);
            int source = node_internal_id_or_add(sqlite3_column_int64(stmt, 0), tmp_map) + offset; 
            int target = node_internal_id_or_add(sqlite3_column_int64(stmt, 1), tmp_map) + offset; 

                prop.length = length;
                prop.cost = direct_cost(stmt, Subway);
                prop.first = source;
                prop.second = target;
                prop.mode = Subway;
                *ii++ = prop;

                prop.length = length;
                prop.cost = reverse_cost(stmt, Subway);
                prop.first = target;
                prop.second = source;
                prop.mode = Subway;
                *ii++ = prop;
            }
        }

        std::cout << "Read the subway layer " << std::endl;

        for( mi = tmp_map.begin(); mi != tmp_map.end(); mi++ )
        {
            sqlite3_reset(get_node_stmt);
            sqlite3_bind_int64(get_node_stmt, 1, (*mi).first);
            if(sqlite3_step(get_node_stmt) != SQLITE_ROW)
            {
                std::cerr << "Unable to get a node "
                    << "Error " << sqlite3_errcode(db) << ": " << sqlite3_errmsg(db) << std::endl;
                exit(EXIT_FAILURE);
            };
            float lon = sqlite3_column_double(get_node_stmt, 0);
            float lat = sqlite3_column_double(get_node_stmt, 1);

            sqlite3_reset(insert_match2);
            std::cout << "Debug: " << (*mi).second << " " << offset << std::endl;
            sqlite3_bind_int(insert_match2, 1, (*mi).second + offset);
            sqlite3_bind_double(insert_match2, 2, lon);
            sqlite3_bind_double(insert_match2, 3, lat);

            if(sqlite3_step(insert_match2) != SQLITE_DONE)
            {
                std::cerr << "Unable to insert a node "
                    << "Error " << sqlite3_errcode(db) << ": " << sqlite3_errmsg(db) << std::endl;
                exit(EXIT_FAILURE);
            };
        }

        std::cout << "Added subway nodes for match" << std::endl;


        sqlite3_prepare_v2(db, "select lon, lat from metroA", -1, &stmt, NULL);
        while(sqlite3_step(stmt) == SQLITE_ROW)
        {
            float lon = sqlite3_column_double(stmt, 0);
            float lat = sqlite3_column_double(stmt, 1);
            Node matched = match(lon, lat);
            Node matched2 = match(lon, lat, true);
            
            std::cout << "Matched " << matched2.id << "to " << matched.id << std::endl;
            prop.length = 0;
            prop.cost =  FunctionPtr( new Const_cost(30) );
            prop.first = matched2.id;
            prop.second = matched.id;
            prop.mode = Car;
            *ii++ = prop;

            prop.first = matched.id;
            prop.cost =  FunctionPtr( new Const_cost(15) );
            prop.second = matched2.id;
            *ii++ = prop;
            
        }

        std::cout << "Connected both layers" << std::endl;

        sort(edge_prop.begin(), edge_prop.end());

        std::cout << "# Going to create the graph" << std::endl;
        cg = CGraph(edge_prop.begin(), edge_prop.end(), edge_prop.begin(), node_count + offset, edge_prop.size());
        std::cout << "2nd layer = " << node_count << " 1rst layer = " << offset << std::endl;

        std::cout << "# Number of nodes: " << boost::num_vertices(cg) << ", nombre d'arcs : " << boost::num_edges(cg) << std::endl;

        sqlite3_prepare_v2(db, "SELECT lon, lat from nodes WHERE id=?",
                -1, &get_node_stmt, NULL);
        std::map<uint64_t, int>::const_iterator nodes_it;
        for( nodes_it = foot_map.begin(); nodes_it != foot_map.end(); nodes_it++ )
        {
            sqlite3_reset(get_node_stmt);
            sqlite3_bind_int64(get_node_stmt, 1, (*nodes_it).first);
            if(sqlite3_step(get_node_stmt) != SQLITE_ROW)
            {
                std::cerr << "Unable to get node (1) "
                    << "Error " << sqlite3_errcode(db) << ": " << sqlite3_errmsg(db) << std::endl;
                exit(EXIT_FAILURE);
            };
            cg[(*nodes_it).second].id = (*nodes_it).first;
            cg[(*nodes_it).second].lon = sqlite3_column_double(get_node_stmt, 0);
            cg[(*nodes_it).second].lat = sqlite3_column_double(get_node_stmt, 1);
        }
        for( nodes_it = tmp_map.begin(); nodes_it != tmp_map.end(); nodes_it++ )
        {
            sqlite3_reset(get_node_stmt);
            sqlite3_bind_int64(get_node_stmt, 1, (*nodes_it).first);
            if(sqlite3_step(get_node_stmt) != SQLITE_ROW)
            {
                std::cerr << "Unable to get node (2) "
                    << "Error " << sqlite3_errcode(db) << ": " << sqlite3_errmsg(db) << std::endl;
                exit(EXIT_FAILURE);
            };
            cg[(*nodes_it).second + offset].id = (*nodes_it).first;
            cg[(*nodes_it).second + offset].lon = sqlite3_column_double(get_node_stmt, 0);
            cg[(*nodes_it).second + offset].lat = sqlite3_column_double(get_node_stmt, 1);
        }
        std::cout << "# Loading the graph done " << std::endl;
    }

    Shortest_path::Shortest_path(const char * db, Transport_mode m)
    {
        init(db, m);
    }

    std::list<Path_elt> Shortest_path::compute(uint64_t start, uint64_t end, int start_time)
    {
        std::list<Path_elt> path;

        std::vector<cvertex> p(boost::num_vertices(cg));
        std::vector<double> d(boost::num_vertices(cg));

        cvertex start_idx = start;//node_internal_id(start), end_idx = node_internal_id(end);
        cvertex end_idx = end;
        std::cout << "Going to calc from " << start << "=" << start_idx << " to " << end << "=" << end_idx << std::endl;

        ptime epoch(date(1970, Jan, 1), seconds(0));
        ptime now(day_clock::local_day(), seconds(start_time));
        double timestamp = (now - epoch).total_seconds();

        try
        {
            boost::dijkstra_shortest_paths(cg, start_idx,
                    boost::predecessor_map(&p[0])
                    .distance_map(&d[0])
                    .weight_map(get(&Edge_property::cost, cg))
                    .visitor(dijkstra_goal_visitor(end_idx))
                    .distance_combine(Combine_distance())
                    .distance_zero(timestamp)
                    .distance_compare(compare())
                    );
        }
        catch (found_goal fg)
        {
        }
        if (p[end_idx] == end_idx)
            std::cerr << "No predecessor found for " << end_idx << std::endl;
        //path.push_front(end_idx);
        while (p[end_idx] != end_idx)
        {
            cedge cur_edge = boost::edge(p[end_idx], end_idx, cg).first;
            Path_elt el;
            el.source = cg[p[end_idx]];
            el.target = cg[end_idx];
            el.length = cg[cur_edge].length;
            el.duration = d[end_idx] - d[p[end_idx]];
            el.mode = cg[cur_edge].mode;

            path.push_front(el);
            end_idx = p[end_idx];
        }
        return path;
    }

    int Shortest_path::nodes() const
    {
        return node_count;
    }

    Shortest_path::~Shortest_path()
    {
    }

    Node Shortest_path::match(double lon, double lat, bool alt)
    {
        sqlite3_stmt * stmt = match_stmt;
        if(alt)
            stmt = match_stmt2;
        float tol = 0.1;
        Node ret;
        sqlite3_reset(stmt);
        sqlite3_bind_double(stmt, 1, lon - tol);
        sqlite3_bind_double(stmt, 2, lon + tol);
        sqlite3_bind_double(stmt, 3, lat - tol);
        sqlite3_bind_double(stmt, 4, lat + tol);
        sqlite3_bind_double(stmt, 5, lon);
        sqlite3_bind_double(stmt, 6, lat);

        if(sqlite3_step(stmt) != SQLITE_ROW)
        {
            std::cerr << "Match failed lon=" << lon << ", lat=" << lat << std::endl;
            throw Node_not_found();
        }
        else
        {
            ret.id = sqlite3_column_int64(stmt, 0);
            ret.lon = sqlite3_column_double(stmt, 1);
            ret.lat = sqlite3_column_double(stmt, 2);
            return ret;
        }
    }


}
