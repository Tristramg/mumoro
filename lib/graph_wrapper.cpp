#include "graph_wrapper.h"
#include <iostream>

Edge::Edge() : distance(0), elevation(0), mode_change(0), cost(0), line_change(0)
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
        return (start / (24*3600) + 1)  * 24*3600 + timetable.begin()->second;
    }
}


Graph::Graph(int nb_nodes) : g(nb_nodes)
{
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

