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
           case Subway: return (sqlite3_column_int(stmt,7) != 0); break;
           default: return false;
       }
    }

    bool add_reverse(sqlite3_stmt * stmt, Transport_mode m)
    {
       switch(m)
       {
           case Car: return (sqlite3_column_int(stmt, 7) != 0); break;
           case Bike: return (sqlite3_column_int(stmt,5) ); break;
           case Foot: return (sqlite3_column_int(stmt,4) != 0); break;
           case Subway: return (sqlite3_column_int(stmt,8) != 0); break;
           default: return false;
       }
    }




    int Shortest_path::node_internal_id_or_add(uint64_t node_id)
    {
        std::map<uint64_t, int>::const_iterator it = foot_map.find(node_id);
        if (it == foot_map.end())
        {
            foot_map[node_id] = node_count++;
            rev_map[node_count-1] = node_id;
            return (node_count - 1);
        }
        else
        {
            return (*it).second;
        }
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
        sqlite3_stmt * stmt;
        sqlite3_open(db_file, &db);

        sqlite3_prepare_v2(db, "SELECT lon,lat FROM nodes WHERE id = ?", -1, &node_stmt, NULL);

        sqlite3_prepare_v2(db, "select source, target, length, foot, bike, bike_r, car, car_r, subway from links", -1, &stmt, NULL);

       std::vector<Edge_property> edge_prop;
        double cost;
        uint64_t source, target;
        Edge_property prop;

std::back_insert_iterator<std::vector<Edge_property> > ii(edge_prop);

    while(sqlite3_step(stmt) == SQLITE_ROW)
    {
        cost = sqlite3_column_double(stmt,2);
        source = node_internal_id_or_add(sqlite3_column_int64(stmt, 0)); 
        target = node_internal_id_or_add(sqlite3_column_int64(stmt, 1)); 

        prop.length = FunctionPtr(new Const_cost(cost / foot_speed));
        prop.first = source;
        prop.second = target;
        prop.mode = Foot;
        *ii++ = prop;
        prop.length = FunctionPtr(new Const_cost(cost / foot_speed));
        prop.first = target;
        prop.second = source;
        prop.mode = Foot;
        *ii++ = prop;
    }

    sort(edge_prop.begin(), edge_prop.end());

    std::cout << "# Going to create the graph" << std::endl;
    cg = CGraph(edge_prop.begin(), edge_prop.end(), edge_prop.begin(), node_count, edge_prop.size());

    std::cout << "# Number of nodes: " << boost::num_vertices(cg) << ", nombre d'arcs : " << boost::num_edges(cg) << std::endl;
    std::cout << "# Loading the graph done " << std::endl;
    }

    Shortest_path::Shortest_path(const char * db, Transport_mode m) :
        node_count(0)     {
            init(db, m);
        }

    std::list<int> Shortest_path::compute(int start, int end, int start_time)
    {
        std::list<int> path;

        std::vector<cvertex> p(boost::num_vertices(cg));
        std::vector<double> d(boost::num_vertices(cg));

        cvertex start_idx = node_internal_id(start), end_idx = node_internal_id(end);
        std::cout << "Going to calc from " << start << "=" << start_idx << " to " << end << "=" << end_idx << std::endl;

        ptime epoch(date(1970, Jan, 1), seconds(0));
        ptime now(day_clock::local_day(), seconds(start_time));
        int timestamp = (now - epoch).total_seconds();

        try
        {
            boost::dijkstra_shortest_paths(cg, start_idx,
                    boost::predecessor_map(&p[0])
                    .distance_map(&d[0])
                    .weight_map(get(&Edge_property::length, cg))
                    .visitor(dijkstra_goal_visitor(end_idx))
                    .distance_combine(Combine_distance())
                    .distance_zero(timestamp)
                    );
        }
        catch (found_goal fg)
        {
        }
        if (p[end_idx] == end_idx)
            std::cerr << "No predecessor found for " << end_idx << std::endl;
        path.push_front(end_idx);
        while (p[end_idx] != end_idx)
        {
            // cedge cur_edge = boost::edge(p[end_idx], end_idx, cg).first;
            //path.push_front(std::pair<int,int>(cg[cur_edge].link_id, cg[cur_edge].mode));
            end_idx = p[end_idx];
            path.push_front(end_idx);
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

    std::list<std::pair<double, double> >Shortest_path::compute_lon_lat(int s, int e)
    {
        std::list<int> n = compute(s,e);
        std::list<std::pair<double, double> > nodes;
        std::list<int>::iterator i;
        for(i = n.begin(); i != n.end(); i++)
            nodes.push_back(node_lon_lat(rev_map[*i]));
        return nodes;
    }

    std::pair<double, double> Shortest_path::node_lon_lat(uint64_t node_id)
    {
        sqlite3_reset(node_stmt);
        sqlite3_bind_int64(node_stmt, 1, node_id);
        sqlite3_step(node_stmt);
        return std::pair<double,double>(
                sqlite3_column_double(node_stmt, 0),
                sqlite3_column_double(node_stmt, 1));
    }
    Node Shortest_path::match(double lon, double lat)
    {
        float tol = 0.002;
        std::stringstream q;
        q << "SELECT id, lon, lat FROM nodes WHERE lon > " << lon - tol 
            << " AND lon < " << lon + tol
            << " AND lat > " << lat - tol
            << " AND lat < " << lat + tol
            << " ORDER BY abs(lon - " << lon << ")"
            << " + abs(lat - " << lat << ")";
        sqlite3_stmt * stmt;
        sqlite3_prepare_v2(db, q.str().c_str(), -1, &stmt, NULL);
        Node ret;
        if(sqlite3_step(stmt) != SQLITE_ROW)
        {
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
