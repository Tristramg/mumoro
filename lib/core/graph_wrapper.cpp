#include "graph_wrapper.h"
#include <iostream>
#include <fstream>
#include <boost/graph/dijkstra_shortest_paths.hpp>
#include <boost/graph/adj_list_serialize.hpp>

Edge::Edge() : distance(0), elevation(0), mode_change(0), cost(0), line_change(0), co2(0)
{
}

Duration::Duration(float d) : const_duration(d) {}

Duration::Duration() : const_duration(-1) {}

void Duration::append(float start, float arrival, const std::string & services)
{
    BOOST_ASSERT(start < arrival);
    timetable.push_back(Time(start, arrival, Services(services)));
}

float Duration::operator()(float start, int day) const
{
    float next_day = 0;
    int run = 0;
    if (const_duration >= 0)
        return start + const_duration;
    else
    {
        std::vector<Time>::const_iterator it;

        for(it = timetable.begin(); it != timetable.end(); it++)
        {
            float tt_start, tt_arrival;
            Services s;
            boost::tie(tt_start, tt_arrival, s) = *it;
            if (tt_start >= start && s[day])
            {
                return tt_arrival;
            }
            if (next_day != 0 && s[day+1])
            {
                next_day = start + 24*3600;
            }
        }
        if(next_day > 0)
            return next_day;
        else 
        {
            throw No_traffic();
        }
    }
}

Graph::Graph(const std::string & filename)
{
    load(filename);
}

Graph::Graph(int nb_nodes) : g(nb_nodes)
{
}

void Graph::add_edge(int source, int target, const Edge & e)
{
    boost::add_edge(source, target, e, g);
}

bool Graph::public_transport_edge(int source, int target, float start, float arrival, const std::string & services)
{
    edge_t e;
    bool b;
    tie(e, b) = edge(source, target, g);
    if(!b)
    {
        bool c;
        tie(e, c) = boost::add_edge(source, target, g);
    }
    g[e].duration.append(start, arrival, services);
    return !b;
}
    struct found_goal
    {
    }; // exception for termination

    // visitor that terminates when we find the goal

    class dijkstra_goal_visitor : public boost::default_dijkstra_visitor
    {   
        public:
            
            dijkstra_goal_visitor(int goal) : m_goal(goal)
        {
        }   
            
            template <class Graph_t>
                void examine_vertex(int u, Graph_t& g)
                {   
                    if (u == m_goal)
                        throw found_goal();
                }
        private:
            int m_goal;
    };

float calc_duration(float in, Duration d)
{
    return d(in, 0);
}

struct Comp
{
    bool operator()(float a, float b) const {return a<b;}
    bool operator()(const Duration &, float) const {return false;}
};

bool Graph::dijkstra(int source, int target)
{
    std::vector<int> p(boost::num_vertices(g));
    std::vector<float> d(boost::num_vertices(g));
    try{
    boost::dijkstra_shortest_paths(g, source,
            boost::predecessor_map(&p[0])
            .distance_map(&d[0])
            .weight_map(get(&Edge::duration, g))
            .visitor(dijkstra_goal_visitor(target))
            .distance_zero(30000)
            .distance_combine(&calc_duration)
            .distance_compare(Comp())
            );
    return false;
    }
    catch(found_goal)
    {
        return true;
    }

}
    

void Graph::load(const std::string & filename)
{
    std::cout << "Loading graph from file " << filename << std::endl;
    std::ifstream ifile(filename.c_str());
    boost::archive::binary_iarchive iArchive(ifile);
    iArchive >> g; //graph;   
    std::cout << "   " << boost::num_vertices(g) << " nodes" << std::endl;
    std::cout << "   " << boost::num_edges(g) << " edges" << std::endl;
}

void Graph::save(const std::string & filename) const
{
    std::ofstream ofile(filename.c_str());
    boost::archive::binary_oarchive oArchive(ofile);
    oArchive << g;
}


