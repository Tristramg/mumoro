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
    Layer::Layer(int off) : offset(off), count(0) {}

    int Layer::add_node(uint64_t id, double lon, double lat)
    {
        std::map<uint64_t, int>::const_iterator it = nodes_map.find(id);
        if (it == nodes_map.end())
        {
            coord.push_back(std::make_pair(lon, lat));
            nodes_map[id] = offset + count ;
            count++;
            return (offset + count - 1);
        }
        else
        {
            return (*it).second;
        }
    }

    int Layer::match(double lon, double lat)
    {
        double best = INFINITY;
        int best_n = -1;
        for(size_t i=0; i < coord.size(); i++)
        {
            double d = pow((coord[i].first - lon),2) + pow((coord[i].second - lat),2);
            if( d < best )
            {
                best = d;
                best_n = i;
            }
        }
        if( best_n == -1 )
            throw Node_not_found();
        else
            return best_n + offset;
    }

    Node Layer::get(int id) const
    {
        if(id < offset || id >= count + offset)
        {
            std::cout << "offset " << offset << " id " << id <<std::endl;
            throw Node_not_found();
        }
        Node n;
        n.id = id;
        n.lon = coord[id-offset].first;
        n.lat = coord[id-offset].second;
        return n;
    }


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

    int Shortest_path::offset()
    {
        int count = 0;
        std::vector<Layer>::const_iterator i;
        for(i = layers.begin(); i != layers.end(); i++)
            count += (*i).nodes_map.size();
        return count;
    }

    Layer Shortest_path::add_layer(const char * db_file, Transport_mode mode, bool acessible)
    {
        sqlite3 * db;
        sqlite3_open(db_file, &db);
        sqlite3_stmt * stmt;
        sqlite3_prepare_v2(db, "select source, target, length, foot, bike, bike_r, car, car_r, subway, lon1, lat1, lon2, lat2 from links", -1, &stmt, NULL);

        Edge_property prop;
        Layer l(offset());

        std::back_insert_iterator<std::vector<Edge_property> > ii(edge_prop);
        while(sqlite3_step(stmt) == SQLITE_ROW)
        {
            double length = sqlite3_column_double(stmt,2);

            double lon1 = sqlite3_column_double(stmt,9);
            double lat1 = sqlite3_column_double(stmt,10);
            double lon2 = sqlite3_column_double(stmt,11);
            double lat2 = sqlite3_column_double(stmt,12);

            uint64_t sid = sqlite3_column_int64(stmt,0);
            uint64_t tid = sqlite3_column_int64(stmt,1); 

            if( add_direct(stmt, mode) )
            {
                int source = l.add_node(sid, lon1, lat1);
                int target = l.add_node(tid, lon2, lat2);

                prop.length = length;
                prop.cost = direct_cost(stmt, mode);
                prop.first = source;
                prop.second = target;
                prop.mode = mode;
                *ii++ = prop;
            }

            if( add_reverse(stmt, mode) )
            {
                int source = l.add_node(sid, lon1, lat1);
                int target = l.add_node(tid, lon2, lat2);

                prop.length = length;
                prop.cost = reverse_cost(stmt, mode);
                prop.first = target;
                prop.second = source;
                prop.mode = mode;
                *ii++ = prop;
            }
        }
        layers.push_back(l);
        return l;
    }

    void Shortest_path::connect(Layer & a, Layer & b, FunctionPtr down, FunctionPtr up, const std::string db_file, const std::string table)
    {
        std::string q = "SELECT lon, lat FROM ";
        q += table;
        sqlite3 * db;
        sqlite3_stmt * stmt;
        sqlite3_open(db_file.c_str(), &db);
        Edge_property prop;
        sqlite3_prepare_v2(db, q.c_str(), -1, &stmt, NULL);

        while(sqlite3_step(stmt) == SQLITE_ROW)
        {
            double lon = sqlite3_column_double(stmt,0);
            double lat = sqlite3_column_double(stmt,1);
            int matched = a.match(lon, lat);
            int matched2 = b.match(lon, lat);

            prop.length = 0;
            prop.cost =  down;
            prop.first = matched2;
            prop.second = matched;
            prop.mode = Switch;
            edge_prop.push_back(prop);

            prop.first = matched;
            prop.cost =  up;
            prop.second = matched2;
            edge_prop.push_back(prop);
        }


    }

    void Shortest_path::build()
    {
        sort(edge_prop.begin(), edge_prop.end());

        std::cout << "# Going to create the graph" << std::endl;
        cg = CGraph(edge_prop.begin(), edge_prop.end(), edge_prop.begin(), offset(), edge_prop.size());

        std::cout << "# Number of nodes: " << boost::num_vertices(cg) << ", nombre d'arcs : " << boost::num_edges(cg) << std::endl;

        std::vector<Layer>::const_iterator li;
        std::map<uint64_t, int>::const_iterator nodes_it;
        for(li = layers.begin(); li != layers.end(); li++)
        {
            for( nodes_it = (*li).nodes_map.begin(); nodes_it != (*li).nodes_map.end(); nodes_it++ )
            {
                int id = (*nodes_it).second;
                cg[id].id = (*nodes_it).first;
                cg[id].lon = (*li).get(id).lon;
                cg[id].lat = (*li).get(id).lat;
            }
        }
        std::cout << "# Loading the graph done " << std::endl;
    }

    std::list<Path_elt> Shortest_path::compute(cvertex start_idx, cvertex end_idx, int start_time)
    {
        std::list<Path_elt> path;

        std::vector<cvertex> p(boost::num_vertices(cg));
        std::vector<double> d(boost::num_vertices(cg));

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

    Node Shortest_path::match(double lon, double lat)
    {
        int id = layers[0].match(lon, lat);
        return layers[0].get(id);
    }
}
