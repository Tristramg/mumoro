#include "graph.h"
#include "dijkstra.h"

#include <boost/graph/dijkstra_shortest_paths.hpp>

void test(Graph & g, Graph & gc)
{
    int runs = 100;
      srand ( time(NULL) );
    for(int i = 0; i < runs; i++)
    {
        int start = rand() % boost::num_vertices(g.graph);
        int dest = rand() % boost::num_vertices(g.graph);
        std::vector<float> d(boost::num_vertices(g.graph));
        dijkstra_shortest_paths(g.graph, start, distance_map(&d[0]).weight_map(get(&Graph::Edge::cost0, g.graph)));

        float cost = query_mono(start, dest, gc.graph); 
        if(cost > d[dest] + 0.1 || cost < d[dest] - 0.1)
            std::cout << "fuck from " << start << " to " << dest << " cost: " << cost << " vs " << d[dest] << std::endl;
        else 
            std::cout << " ok " << std::endl;
    }
}
