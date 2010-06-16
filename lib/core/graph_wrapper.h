#include <boost/graph/adjacency_list.hpp>
#include <boost/serialization/map.hpp>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/archive/binary_oarchive.hpp>


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

    template<class Archive>
        void serialize(Archive& ar, const unsigned int version)
        {
            ar & const_duration & timetable;
        }

};

struct Node
{
    template<class Archive>
        void serialize(Archive& ar, const unsigned int version)
        {
        }

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
            template<class Archive>
            void serialize(Archive& ar, const unsigned int version)
            {
                ar & distance & elevation & mode_change & line_change & co2 & duration;
            }

};

typedef boost::adjacency_list<boost::listS, boost::vecS, boost::directedS, Node, Edge > Graph_t;
typedef boost::graph_traits<Graph_t>::edge_descriptor edge_t;

struct Graph
{
    Graph_t g;
    Graph(int nb_nodes);
    Graph(const std::string & filename);
    void add_edge(int source, int target, const Edge & e);
    bool public_transport_edge(int source, int target, float start, float arrival);
    bool dijkstra(int source, int target);
    void save(const std::string & filename) const;
    void load(const std::string & filename);
};

const int invalid_node = -1;

#endif
