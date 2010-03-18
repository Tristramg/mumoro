#include "graph.h"
#include "dijkstra.h"

#include <boost/graph/dijkstra_shortest_paths.hpp>

void test(Graph<2> & g, Graph<2> & gc)
{
    int runs = 0;
    for(int i = 0; i < runs; i++)
    {
        int start = rand() % boost::num_vertices(g.graph);
        int dest = rand() % boost::num_vertices(g.graph);
        std::vector<float> d(boost::num_vertices(g.graph));
        dijkstra_shortest_paths(g.graph, start, distance_map(&d[0]).weight_map(get(&Graph<2>::Edge::cost0, g.graph)));

        float cost = query_mono< Graph<2> >(start, dest, gc.graph); 
        if(cost > d[dest] + 0.1 || cost < d[dest] - 0.1)
            std::cout << "fuck from " << start << " to " << dest << " cost: " << cost << " vs " << d[dest] << std::endl;
    }
}
