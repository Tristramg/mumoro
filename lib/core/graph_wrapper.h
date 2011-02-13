/*    This file is part of Mumoro.

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

    © Université de Toulouse 1 2010
    Author: Tristram Gräbener*/

#include <boost/graph/adjacency_list.hpp>
#include <boost/serialization/vector.hpp>
#include <boost/serialization/map.hpp>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/archive/binary_oarchive.hpp>

#include <boost/tuple/tuple.hpp>
#include <bitset>

#ifndef GRAPH_WRAPPER_H

#define GRAPH_WRAPPER_H

typedef enum {Foot, Bike, Car, PublicTransport} Mode;
typedef std::bitset<128> Services;
typedef boost::tuple<float, float, Services> Time;


struct No_traffic{};

namespace boost { namespace serialization {
template <class Archive>
void save(Archive &ar, const Time &t, const unsigned int version)
{
    ar << boost::get<0>(t);
    ar << boost::get<1>(t);
    std::string s = boost::get<2>(t).to_string();
    ar << s;
}

template <class Archive>
void load(Archive &ar, Time &t, const unsigned int version)
{
    ar >> boost::get<0>(t);
    ar >> boost::get<1>(t);
    std::string s;
    ar >> s;
    boost::get<2>(t) = Services(s);
}

template <class Archive>
void serialize(Archive &ar, Time &t, const unsigned int version)
{
        boost::serialization::split_free(ar, t, version);
}
}
} 

struct Duration
{
    int const_duration;
    std::vector<Time> timetable;
    Duration();
    Duration(float const_duration);
    void append(float start, float arrival, const std::string & services);
    void sort();
    float operator()(float start_time, int day) const;

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
    float penibility;
    Duration duration;
            template<class Archive>
            void serialize(Archive& ar, const unsigned int version)
            {
                ar & distance & elevation & mode_change & line_change & co2 & penibility & duration;
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
    bool public_transport_edge(int source, int target, float start, float arrival, const std::string & services);
    bool dijkstra(int source, int target);
    void save(const std::string & filename) const;
    void load(const std::string & filename);
    void sort();
    int get_start(int source, int target, float time, int day);
    int get_arrival(int source, int target, float time, int day);
};

const int invalid_node = -1;

#endif
