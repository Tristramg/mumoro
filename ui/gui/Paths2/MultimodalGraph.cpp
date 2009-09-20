#include "MultimodalGraph.h"
#include <fstream>
#include <boost/spirit/include/classic_core.hpp>

using namespace boost::spirit::classic;
struct not_accessible{};
struct unknown_mode{};

double rad(double deg)
{
    return deg * 3.14159265 / 180;
}


double distance(double lon1, double lat1, double lon2, double lat2)
{
    const double r = 6371000;

    return acos( sin( rad(lat1) ) * sin( rad(lat2) ) +
                 cos( rad(lat1) ) * cos( rad(lat2) ) * cos( rad(lon2-lon1 ) )
                 ) * r;
}

float cost(float length, Mode m)
{
    switch(m)
    {
        case Foot: return 0; break;
        case Bike: return length * 0.01 / 1000; break;
        case Car: return length * 0.2 / 1000; break;
        case PublicTransport : return length * 0.05 / 1000; break;
    }
}

float duration(int property, float length, Mode m)
{
    switch(m)
    {
    case Foot:
        if(property == 0)
            throw not_accessible();
        return 5 * length / 3.5;
        break;
    case Bike:
        if(property == 0)
            throw not_accessible();
        else
            return length / 4.2;
        break;
    case Car:
        switch(property)
        {
        case 1: return 20 * length / 3.6; break;
        case 2: return 30 * length / 3.6; break;
        case 3: return 50 * length / 3.6; break;
        case 4: return 90 * length / 3.6; break;
        case 5: return 100 * length / 3.6; break;
        case 6: return 120 * length / 3.6; break;
        default: throw not_accessible();
        }
        break;
    default: throw unknown_mode();
    }
}


float bike_comfort(int bike_property, int car_property, float length)
{
    switch(bike_property)
    {
    case 1:
    case 3: return length; break;
    case 2: return car_property * length; break;
    case 4: return length * 1.5; break;
    case 5: return 0.5 * length; break;
    default: throw not_accessible();
    }
}

std::pair<size_t, size_t> MultimodalGraph::load(const std::string & layer, const std::string &nodes, const std::string & edges, Mode m)
{
    size_t nb_nodes = load_nodes(layer, nodes, m);
    size_t nb_edges = load_edges(layer, edges, m);
    return std::make_pair(nb_nodes, nb_edges);
}


size_t MultimodalGraph::load_edges(const std::string & layer, const std::string & edges_file, Mode m)
{
    size_t count = 0;
    std::string s;
    std::ifstream edgesf(edges_file.c_str());
    getline(edgesf, s); // we skip the header
    std::string id, source, target;
    rule <> csv_string = (*(anychar_p - ","));

    if(m == PublicTransport)
    {
        std::string trip_id = "";
        std::string prev_trip_id = "";
        int arrival_time_s = 0, arrival_time_m = 0, arrival_time_h = 0;
        int departure_time_s = 0, departure_time_m = 0,  departure_time_h = 0;
        int prev_departure_time = 0;
        int stop_sequence = 0;
        int prev_stop_sequence = 0;
        node_t prev_node = 0;
        rule<> stop_times_rule = csv_string[assign_a(trip_id)] >> "," >>

                                 int_p[assign_a(arrival_time_h)] >> ":" >>
                                 int_p[assign_a(arrival_time_m)] >> ":" >>
                                 int_p[assign_a(arrival_time_s)] >> "," >>

                                 int_p[assign_a(departure_time_h)] >> ":" >>
                                 int_p[assign_a(departure_time_m)] >> ":" >>
                                 int_p[assign_a(departure_time_s)] >> "," >>

                                 csv_string[assign_a(id)] >> "," >>
                                 int_p[assign_a(stop_sequence)] >> "," >>
                                 csv_string;

        while( getline(edgesf, s) )
        {
            if(!parse(s.c_str(), stop_times_rule, space_p).hit)
                std::cerr << " Parsing error (stop times). Line was: " << s << std::endl;
            else
            {
                int departure_time = departure_time_h * 3600 + departure_time_m * 60 + departure_time_s;
                int arrival_time = arrival_time_h * 3600 + arrival_time_m * 60 + arrival_time_s;
                if(prev_trip_id == trip_id)
                {
                    if( !layers[layer].exists(id) )
                        std::cerr << "Unknown stop_id " << id << std::endl;
                    node_t cur_node = layers[layer][id];
                    edge_t e;
                    bool b;
                    tie(e, b) = edge(prev_node, cur_node, g);
                    if(!b)
                    {
                        Edge ep;
                        ep.nb_changes = 0;
                        ep.distance = distance( g[prev_node].lon, g[prev_node].lat, g[cur_node].lon, g[cur_node].lat);
                        ep.elevation = 0;
                        ep.nb_changes = 0;
                        ep.cost = cost(ep.distance, m);
                        tie(e, b) = add_edge(prev_node, cur_node, ep, g);
                        count++;
                    }
                    g[e].duration.append(prev_departure_time, arrival_time);
                }
                prev_trip_id = trip_id;
                prev_stop_sequence = stop_sequence;
                prev_departure_time = departure_time;
                prev_node = layers[layer][id];
            }
        }
    }

    else
    {
        float length;
        int car, car_reverse, bike, bike_reverse, foot;
        rule<> edges_rules = csv_string[assign_a(id)] >> ',' >>
                             csv_string[assign_a(source)] >> ',' >>
                             csv_string[assign_a(target)] >> ',' >>
                             real_p[assign_a(length)] >> ',' >>
                             int_p[assign_a(car)] >> ',' >>
                             int_p[assign_a(car_reverse)] >> ',' >>
                             int_p[assign_a(bike)] >> ',' >>
                             int_p[assign_a(bike_reverse)] >> ',' >>
                             int_p[assign_a(foot)];

        int property = 0, rev_property = 0;

        while( getline(edgesf,s) )
        {
            if(!parse(s.c_str(), edges_rules, space_p).hit)
                std::cerr << " Parsing error. Line was: " << s << std::endl;
            else
            {
                switch(m)
                {
                case Foot: property = foot; rev_property = foot; break;
                case Bike: property = bike; rev_property = bike_reverse; break;
                case Car: property = car; rev_property = car_reverse; break;
                default: property = 0; rev_property = 0; break;
                }
                Edge e;
                e.nb_changes = 0;
                node_t source_n = layers[layer][source];
                node_t target_n = layers[layer][target];
                e.distance = length;
                e.cost = cost(length, m);

                try
                {
                    if(m == Bike)
                        e.elevation = std::max(0, g[target_n].elevation - g[source_n].elevation);
                    else
                        e.elevation = 0;
                    e.duration = Duration(duration(property, length, m));
                    add_edge(source_n, target_n, e, g);
                    count++;
                }
                catch(not_accessible e) {}

                try
                {
                    if(m == Bike)
                        e.elevation = std::max(0, g[source_n].elevation - g[target_n].elevation);
                    else
                        e.elevation = 0;
                    e.duration = Duration(duration(rev_property, length, m));
                    add_edge(target_n, source_n, e, g);
                    count++;
                }
                catch(not_accessible e) {}
            }
        }
    }
    edgesf.close();
    return count;
}

size_t MultimodalGraph::load_nodes(const std::string & layer, const std::string & nodes_file, Mode m)
{
    size_t count = 0;
    std::string s;
    std::ifstream nodesf(nodes_file.c_str());
    if( !nodesf )
    {
        std::cerr << "An error occured trying to open file " << nodes_file << std::endl;
    }
    getline(nodesf, s); // We skip the header
    std::string id;
    float lon, lat;
    int elevation = 0;
    rule <> csv_string = (*(anychar_p - ","));
    rule <> nodes_rule;
    if( m == PublicTransport)
    {
        nodes_rule = csv_string[assign_a(id)] >> "," >>
                     csv_string >> "," >>
                     csv_string >> "," >>
                     real_p[assign_a(lat)] >> "," >>
                     real_p[assign_a(lon)] >> "," >>
                     csv_string >> "," >>
                     csv_string ;
    }
    else
    {
        nodes_rule = csv_string[assign_a(id)] >> ',' >>
                     real_p[assign_a(lon)] >> ',' >>
                     real_p[assign_a(lat)] >> ',' >>
                     int_p[assign_a(elevation)];
    }

    while( getline(nodesf, s) )
    {
        if(!parse(s.c_str(), nodes_rule, space_p).full)
            std::cerr << " Parsing error. Line was: " << s << std::endl;
        else
        {
            Node n;
            n.layer = layer;
            n.id = id;
            n.lat = lat;
            n.lon = lon;
            n.elevation = elevation;
            node_t new_node = add_vertex(n, g);
            layers[layer][id] = new_node;
            layers[layer].append(lon, lat, new_node);
            count++;
        }
    }
    nodesf.close();
    return count;
}


size_t MultimodalGraph::connect_same_nodes(const std::string & layer1, const std::string & layer2, Edge edge_properties, bool bidirectionnal)
{
    Matching::const_iterator it;
    size_t count = 0;
    for(it = layers[layer1].begin(); it != layers[layer1].end(); it++)
    {
        if(layers[layer2].exists(it->first))
        {
            add_edge(it->second, layers[layer2][it->first], edge_properties, g);
            count++;
            if(bidirectionnal)
            {
                add_edge(layers[layer2][it->first], it->second, edge_properties, g);
                count++;
            }
        }
    }
    return count;
}

size_t MultimodalGraph::connect_closest(const std::string & layer1, const std::string & layer2, Edge edge_properties, bool bidirectionnal)
{
    Matching::const_iterator it;
    size_t count = 0;
    for(it = layers[layer1].begin(); it != layers[layer1].end(); it++)
    {
        try
        {
            node_t nearest = layers[layer2].match(g[it->second].lon, g[it->second].lat);

            add_edge(it->second, nearest, edge_properties, g);
            count++;
            if(bidirectionnal)
            {
                add_edge(nearest, it->second, edge_properties, g);
                count++;
            }
        }
        catch(match_failed) {}
    }
    return count;
}


const Graph_t & MultimodalGraph::graph() const
{
    return this->g;
}

Matching & MultimodalGraph::operator[](const std::string & layer)
{
    return this->layers[layer];
}

Node & MultimodalGraph::operator [](node_t node)
{
    return this->g[node];
}

Duration::Duration(int d) : const_duration(d) {}

Duration::Duration() : const_duration(-1) {}

void Duration::append(int start, int arrival)
{
    timetable[start] = arrival;
}

int Duration::operator()(int start) const
{
    if (const_duration >= 0)
        return start + const_duration;
    else
    {
        if(timetable.size() == 0)
            std::cout << "Timetable is empty !!" <<  std::endl;
        std::map<int, int>::const_iterator it = timetable.upper_bound(start);
        if(it == timetable.end())
        {
            return (start / (24*3600) + 1)  * 24*3600 + timetable.begin()->second;
        }
        else
        {
            return it->second;
        }
    }
}

void Matching::append(float lon, float lat, node_t node)
{
    this->nodes[std::make_pair(lon, lat)] = node;
}

node_t Matching::match(float lon, float lat) const
{
    double best = 180*180 + 90*90;
    node_t best_n = 0;
    std::map<std::pair<float,float>, node_t>::const_iterator it;
    for(it = this->nodes.begin(); it != this->nodes.end(); it++)
    {
        double d = distance(lon, lat, it->first.first, it->first.second);
        if( d < best )
        {
            best = d;
            best_n = it->second;
        }
    }
    if(best > 200)
        throw match_failed();
    return best_n;
}

node_t & Matching::operator [](const std::string & n)
{
    return this->node_map[n];
}

bool Matching::exists(const std::string & node) const
{
    return this->node_map.find(node) != this->node_map.end();
}

Matching::const_iterator Matching::begin() const
{
    return this->node_map.begin();
}

Matching::const_iterator Matching::end() const
{
    return this->node_map.end();
}
