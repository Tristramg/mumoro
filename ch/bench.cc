#include "dijkstra.h"

#include <boost/graph/dijkstra_shortest_paths.hpp>
void bench(Graph<2> & g, Graph<2> & gc)
{

    int runs = 1000;
    std::vector<int> starts(runs);
    std::vector<int> dests(runs);
    for(int i=0; i < runs; i++)
    {
        starts[i] = rand() % boost::num_vertices(g.graph);
        dests[i] = rand() % boost::num_vertices(g.graph);
    }
   /* { 
        boost::progress_timer t;
        for(int i=0; i < runs; i++)
        {
            dijkstra_shortest_paths(g.graph, starts[i], weight_map(get(&Graph<2>::Edge::cost0, g.graph)));
        }
    }
 */
     {
        boost::progress_timer t;
        for(int i=0; i < runs; i++)
        {
            query_mono< Graph<2> >(starts[i], dests[i], gc.graph);
        }
    } 
}
