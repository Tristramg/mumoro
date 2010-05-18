#include "graph_wrapper.h"
#include <iostream>
#include <boost/graph/dijkstra_shortest_paths.hpp>
#include <boost/graph/astar_search.hpp>
#include <math.h>    // for sqrt

using namespace boost;

Edge::Edge() : distance(0), elevation(0), mode_change(0), cost(0), line_change(0), co2(0)
{
}

Duration::Duration(float d) : const_duration(d) {}

Duration::Duration() : const_duration(-1) {}

void Duration::append(float start, float arrival)
{
    timetable[start] = arrival;
}

float Duration::operator()(float start) const
{
    if (const_duration >= 0)
        return start + const_duration;
    else
    {
        std::map<float, float>::const_iterator it;

        for(it = timetable.begin(); it != timetable.end(); it++)
        {
            if (it->first >= start)
                return it->second;
        }
        //it = timetable.lower_bound(start);
        //if(it->first >= start)
        //    return it->second;
        //else
            return (start / (24*3600) + 1)  * 24*3600 + timetable.begin()->second;
    }
}


Graph::Graph(int nb_nodes) : g(nb_nodes)
{
}

void Graph::set_coord(int node, float x, float y)
{
    Node n;
    n.x = x;
    n.y = y;
    g[node] = n;
}

void Graph::add_edge(int source, int target, const Edge & e)
{
    boost::add_edge(source, target, e, g);
}

bool Graph::public_transport_edge(int source, int target, float start, float arrival)
{
    edge_t e;
    bool b;
    tie(e, b) = edge(source, target, g);
    if(!b)
    {
        bool c;
        tie(e, c) = boost::add_edge(source, target, g);
    }
    g[e].duration.append(start, arrival);
    return !b;
}
    struct found_goal
    {
    }; // exception for termination

    // visitor that terminates when we find the goal
int visited;

class dijkstra_goal_visitor : public boost::default_dijkstra_visitor
{   
    public:

        dijkstra_goal_visitor(int goal) : m_goal(goal)
    {
    }   

        template <class Graph_t>
            void examine_vertex(int u, Graph_t&)
            {   
                visited++;
                if (u == m_goal)
                {
                    throw found_goal();
                }
            }
    private:
        int m_goal;
};


// visitor that terminates when we find the goal
class astar_goal_visitor : public boost::default_astar_visitor
{
    public:
        astar_goal_visitor(int goal) : m_goal(goal) {}
        template <class Graph_t>
            void examine_vertex(int u, Graph_t& g) {
                visited++;
                if(u == m_goal)
                {
                    throw found_goal();
                }
            }
    private:
        int m_goal;
};


float calc_duration(float in, Duration d)
{
    return d(in);
}

struct Comp
{
    bool operator()(float a, float b) const {return a<b;}
    bool operator()(const Duration &, float) const {return false;}
};

int Graph::dijkstra(int source, int target)
{
    visited = 0;
    std::vector<float> d(boost::num_vertices(g));
    dijkstra_goal_visitor vis(target);
    if(target >= 0)
    {
        try{
            boost::dijkstra_shortest_paths(g, source,
                    boost::distance_map(&d[0])
                    .weight_map(get(&Edge::duration, g))
                    .visitor(vis)
                    .distance_zero(30000)
                    .distance_combine(&calc_duration)
                    .distance_compare(Comp())
                    );
        }
        catch(found_goal)
        {
        }
    }
    else
    {
        boost::dijkstra_shortest_paths(g, source,
                distance_map(&d[0])
                .weight_map(get(&Edge::duration, g))
                .visitor(vis)
                .distance_zero(30000)
                .distance_combine(&calc_duration)
                .distance_compare(Comp())
                );
    }
    return visited;
}


int Graph::dijkstra_dist(int source, int target)
{
    visited = 0;
    dijkstra_goal_visitor vis(target);
    std::vector<float> d(boost::num_vertices(g));
    if(target >= 0)
    {
        try{
            boost::dijkstra_shortest_paths(g, source,
                    distance_map(&d[0])
                    .weight_map(get(&Edge::distance, g))
                    .visitor(vis)
                    );
        }
        catch(found_goal)
        {
        }
    }
    else
    {
        boost::dijkstra_shortest_paths(g, source,
                distance_map(&d[0])
                .weight_map(get(&Edge::distance, g))
                .visitor(vis)
                .distance_zero(30000)
                );
    }
    return visited;
}


class distance_heuristic : public astar_heuristic<Graph_t, float>
{
    public:
        distance_heuristic(Graph & gr, int goal)
            : g(gr), m_goal(goal){}
        float operator()(int u)
        {
            return g.distance(u, m_goal) / 16; //environ 55km/h vitesse moyenne du bart
        }
    private:
        Graph & g;
        int m_goal;
};


int Graph::astar(int source, int target)
{

    visited = 0;
    std::vector<float> d(boost::num_vertices(g));
    std::vector<float> r(boost::num_vertices(g));
    astar_goal_visitor vis(target);
    try
    {
        astar_search
            (g, source,
             distance_heuristic(*this, target),
             distance_map(&d[0])
             .rank_map(&r[0])
             .visitor(vis)
             .weight_map(get(&Edge::duration, g))
             .distance_zero(30000)
             .distance_combine(&calc_duration)
             .distance_compare(Comp())
            );
    }
    catch(found_goal)
    {}
    return visited;
}
double rad(double deg)
{
    return deg * 3.14159265 / 180;
}


float Graph::distance(int source, int target)
{
    const double r = 6371000;

    float lon1 = g[source].x;
    float lon2 = g[target].x;
    float lat1 = g[source].y;
    float lat2 = g[target].y;
    return acos( sin( rad(lat1) ) * sin( rad(lat2) ) +
            cos( rad(lat1) ) * cos( rad(lat2) ) * cos( rad(lon2-lon1 ) )
            ) * r;
}
