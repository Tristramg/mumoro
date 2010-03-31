#include "dijkstra.h"
#include "query.h"

#include <boost/graph/dijkstra_shortest_paths.hpp>

struct found_goal{};

class my_dijkstra_visitor : public boost::default_dijkstra_visitor
{
public:

    int count;
    int m_goal;
    my_dijkstra_visitor(int goal) : count(0), m_goal(goal)
    {
    }

    template <class CGraph>
    void examine_vertex(int u, CGraph&)
    {
        count++;
        if (u == m_goal)
        {
            std::cout << "Dijkstra visited: " << count << "  ";
            throw found_goal();
        }
    }
};
void bench(Graph & g, Graph & gc)
{

    int runs = 100;
    std::vector<int> starts(runs);
    std::vector<int> dests(runs);
    for(int i=0; i < runs; i++)
    {
        starts[i] = rand() % boost::num_vertices(g.graph);
        dests[i] = rand() % boost::num_vertices(g.graph);
    }
    { 
        boost::progress_timer t;
        for(int i=0; i < runs; i++)
        {
            my_dijkstra_visitor counter(dests[i]);
            try
            {
                dijkstra_shortest_paths(g.graph, starts[i], weight_map(get(&Graph::Edge::cost0, g.graph)).visitor(counter));
            }
            catch(found_goal fg)
            {
                query_mono(starts[i], dests[i], gc.graph);
                std::cout << std::endl;
            }
        }
    }

    {
        boost::progress_timer t;
        for(int i=0; i < runs; i++)
        {
            //query_mono(starts[i], dests[i], gc.graph);
        }
    } 
}

void martins_bench(Graph & g, Graph & gc)
{
    int runs = 100;
    std::vector<int> starts(runs);
    std::vector<int> dests(runs);
    for(int i=0; i < runs; i++)
    {
        starts[i] = rand() % boost::num_vertices(g.graph);
        dests[i] = rand() % boost::num_vertices(g.graph);
    }
    { 
        boost::progress_timer t;
        for(int i=0; i < runs; i++)
        {
            martins(starts[i], dests[i], g);
        }
    }

    {
        boost::progress_timer t;
        for(int i=0; i < runs; i++)
        {
            ch_martins(starts[i], dests[i], gc);
        }
    }
 
}
