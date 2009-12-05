#include "tsaggouris.h"

#include <math.h>
#include <boost/array.hpp>
#include <boost/numeric/ublas/matrix.hpp>

using namespace boost;
using namespace boost::numeric::ublas;
//typedef std::pair<size_t, size_t> pos;
typedef size_t pos;

struct Label
{
    array<float, 2> cost;
};
float log11;
void extend_n_merge(std::map<pos, Label> & R, const std::map<pos, Label> & Q, const edge_t & e, Graph & g)
{
    for(std::map<pos, Label>::const_iterator it = Q.begin(); it != Q.end(); it++)
    {
        Label q;
        q.cost = it->second.cost;
        q.cost[0] = g.g[e].duration(q.cost[0]);
        q.cost[1] = q.cost[1] + g.g[e].elevation;

        pos new_pos(floor(log(q.cost[1] + 1.1)/log11));
        if( R.find(new_pos) == R.end() || R[new_pos].cost[0] > q.cost[0] )
        {
            R[new_pos] = q;
        }
    }
}

void ssmosp(Graph & g, int start)
{
    log11 = log(11);
    Label null;
    null.cost[0] = 30000;
    null.cost[1] = 0;
    size_t nodes = num_vertices(g.g);
    vector<std::map<pos, Label> > P(nodes);
    P[start][0] = null;

    for(size_t i = 1; i < nodes; i++)
    {
        std::cout << "New round ! (" << i << "/" << nodes - 1 << ")" << std::endl;
        Graph_t::edge_iterator e, e_end;
        tie(e, e_end) = edges(g.g);
        for(; e != e_end; e++)
        {
            extend_n_merge(P[target(*e, g.g)], P[source(*e, g.g)], *e, g);
        }
    }

    size_t total = 0;
    for(int n = 0; n<nodes; n++)
    {
        total += P[n].size();
    }

    std::cout << "Number of elements found " << total << std::endl;
}

