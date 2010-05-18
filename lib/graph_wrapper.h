#include <boost/graph/adjacency_list.hpp>

#ifndef GRAPH_WRAPPER_H
#define GRAPH_WRAPPER_H

typedef enum {Foot, Bike, Car, PublicTransport} Mode;

class Duration
{
    int const_duration;
    std::map<float, float> timetable;
public:
    Duration();
    Duration(float const_duration);
    void append(float start, float arrival);
    float operator()(float start_time) const;
};

struct Node
{
    float x;
    float y;
};

struct Edge
{
    Edge();
    float distance;
    float elevation;
    float mode_change;
    float cost;
    float line_change;
    float co2;
    Duration duration;
};

typedef boost::adjacency_list<boost::listS, boost::vecS, boost::directedS, Node, Edge > Graph_t;
typedef boost::graph_traits<Graph_t>::edge_descriptor edge_t;

struct Graph
{
    Graph_t g;
    Graph(int nb_nodes);
    void add_edge(int source, int target, const Edge & e);
    void set_coord(int node, float x, float y);
    bool public_transport_edge(int source, int target, float start, float arrival);
    int dijkstra(int source, int target = -1);
    int dijkstra_dist(int source, int target = -1);
    int astar(int source, int target);
    float distance(int source, int target);
};

const int invalid_node = -1;

#endif
