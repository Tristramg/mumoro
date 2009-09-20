#include <string>
#include <map>
#include <iostream>
#include <boost/graph/adjacency_list.hpp>
//#include <tr1/functional_hash.h>
#include <boost/functional/hash.hpp>
#include <ext/hash_map>
#include <limits.h>

#ifndef MULTIMODALGRAPH_H
#define MULTIMODALGRAPH_H

typedef enum {Foot, Bike, Car, PublicTransport} Mode;

double distance(double lon1, double lat1, double lon2, double lat2);

struct match_failed {};

class Duration
{
    int const_duration;
    std::map<int, int> timetable;
public:
    Duration();
    Duration(int const_duration);
    void append(int start, int arrival);
    int operator()(int start_time) const;
};


struct Node
{
    std::string id;
    int elevation;
    float lon;
    float lat;
    std::string layer;
};

struct Edge
{
    float distance;
    float elevation;
    float nb_changes;
    float cost;
    Duration duration;
};

typedef boost::adjacency_list<boost::listS, boost::vecS, boost::directedS, Node, Edge > Graph_t;
typedef boost::graph_traits<Graph_t>::vertex_descriptor node_t;
typedef boost::graph_traits<Graph_t>::edge_descriptor edge_t;

typedef __gnu_cxx::hash_map<std::string, node_t, boost::hash< std::string > > node_map_t;

static const node_t invalid_node = std::numeric_limits<node_t>::max();

class Matching
{
private:
    std::map<std::pair<float,float>, node_t> nodes;
    node_map_t node_map;
public:
    typedef node_map_t::const_iterator const_iterator;
    node_t match(float lon, float lat) const;
    void append(float lon, float lat, node_t node);
    node_t & operator[](const std::string & node);
    bool exists(const std::string & node) const;
    const_iterator begin() const;
    const_iterator end() const;
};

class MultimodalGraph
{
private:
    Graph_t g;
    std::map<std::string, Matching> layers;
    size_t load_edges(const std::string & layer, const std::string & edges, Mode m);
    size_t load_nodes(const std::string & layer, const std::string & nodes, Mode m);

public:
    const Graph_t & graph() const;

    std::pair<size_t, size_t>
            load (const std::string & layer,
                 const std::string & nodes,
                 const std::string & edges,
                 Mode m = Foot);

    size_t connect_same_nodes(const std::string & layer1, const std::string & layer2, Edge edge_properties, bool bidirectionnal = true);
    size_t connect_closest(const std::string & layer1, const std::string & layer2, Edge edge_properties, bool bidirectionnal = true);
    //$.void connect_same_nodes(const std::string & layer1, const std::string & layer2, Edge edge_properties, bool bidirectionnal = true);

    Matching & operator[](const std::string & layer_name);
    Node & operator[](node_t);
};
#endif // MULTIMODALGRAPH_H
