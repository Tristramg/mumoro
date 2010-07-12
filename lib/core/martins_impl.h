#ifndef MARTINS_IMPL_H
#define MARTINS_IMPL_H

#include "martins.h"

#include <iostream>
#include <string>
#include <fstream>
#include <deque>
#include <boost/spirit/include/classic_core.hpp>
#include <boost/multi_index_container.hpp>
#include <boost/multi_index/ordered_index.hpp>
#include "boost/multi_index/hashed_index.hpp"
#include <boost/multi_index/member.hpp>
#include <boost/array.hpp>

using namespace boost::multi_index;
using namespace boost::spirit::classic;
using namespace boost;
using namespace std;

float delta(float a, float b);

template<size_t N>
struct Label
{
    int node;
    array<float, N> cost;
    int pred;
    size_t pred_idx;

    bool operator==(const Label & l)
    {
        return pred == l.pred && cost == l.cost;
    }

    bool operator<(const Label & l)
    {
        return cost < l.cost;
    }
};

template<size_t N>
struct Dominates
{
    bool operator()(const Label<N> & a, const Label<N> & l) const
    {
        bool strict = false;
        for(size_t i = 0; i < N; i++)
        {
            if(a.cost[i] > l.cost[i])
                return false;
            if(!strict && a.cost[i] < l.cost[i])
                strict = true;
        }
        return strict;
    }
};

template<size_t N>
struct Relaxed_dominates
{
};

template<>
struct Relaxed_dominates<2>
{
    float r1;
    Relaxed_dominates(float r1) : r1(r1) {}

    bool operator()(const Label<2> & a, const Label<2> & l) const
    {
        float gain1 = l.cost[0] - a.cost[0];
        float gain2 = l.cost[1] - a.cost[1];

        if(gain1 >= 0)
        { 
            if(gain2 >= 0 || -gain1/gain2 >= r1)
                return true;
        }
        return false;
    }
};

template<>
struct Relaxed_dominates<3>
{
    float r1,r2;
    Relaxed_dominates(float r1, float r2) : r1(r1), r2(r2) {}

    bool operator()(const Label<3> & a, const Label<3> & l) const
    {
        float gain1 = l.cost[0] - a.cost[0];
        float gain2 = l.cost[1] - a.cost[1];
        float gain3 = l.cost[2] - a.cost[2];

        if(gain1 >= 0)
        { 
            if(gain2 >= 0 || -gain1/gain2 >= r1)
            {
                if(gain3 >= 0 || -gain1/gain3 >= r2)
                    return true;
            }
        }
        return false;
    }
};

template<>
struct Relaxed_dominates<4>
{
    float r1,r2,r3;
    Relaxed_dominates(float r1, float r2, float r3) : r1(r1), r2(r2), r3(r3) {}

    bool operator()(const Label<4> & a, const Label<4> & l) const
    {
        float gain1 = l.cost[0] - a.cost[0];
        float gain2 = l.cost[1] - a.cost[1];
        float gain3 = l.cost[2] - a.cost[2];
        float gain4 = l.cost[3] - a.cost[3];

        if(gain1 >= 0)
        { 
            if(gain2 >= 0 || -gain1/gain2 >= r1)
            {
                if(gain3 >= 0 || -gain1/gain3 >= r2)
                {
                    if(gain4 >= 0 || -gain1/gain4 >= r3)
                        return true;
                }
            }
        }
        return false;
    }
};




template<size_t N>
        struct my_queue
{

    typedef multi_index_container<
            Label<N>,
            indexed_by<
            ordered_non_unique<member<Label<N>, array<float, N>, &Label<N>::cost> >,
            hashed_non_unique<member<Label<N>, int, &Label<N>::node > >
            >
            > Type;

    typedef typename nth_index<Type, 0>::type& by_cost;
    typedef typename nth_index<Type, 1>::type& by_nodes;
    typedef typename nth_index<Type, 0>::type::iterator cost_it;
    typedef typename nth_index<Type, 1>::type::iterator nodes_it;
};



template<size_t N>
ostream & operator<<(ostream & os, Label<N> l)
{
    os << "Label[" << l.node << "-" << l.pred<< "] {";
    for(size_t i=0; i<N; i++)
        os << l.cost[i] << " ";
    os << "}";
    return os;
}

template<size_t N, typename Comp>
bool is_dominated_by_any(const typename my_queue<N>::Type & Q, const Label<N> & l, Comp c)
{
    typename my_queue<N>::nodes_it it, end;
    tie(it, end) = Q.get<1>().equal_range(l.node);
    for(; it != end; it++)
    {
        if( c(*it, l) || it->cost == l.cost)
            return true;
    }
    return false;
}

template<size_t N>
        bool is_dominated_by_any(const typename my_queue<N>::Type & Q, const Label<N> & l)
{
    return is_dominated_by_any(Q, l, Dominates<N>());
}

template<size_t N, typename Comp>
bool is_dominated_by_any(const deque< Label<N> > & llist, const Label<N> & l, Comp c)
{
    typedef typename deque< Label<N> >::const_iterator Iterator;
    for(Iterator it = llist.begin(); it != llist.end(); it++)
    {
        if(c(*it, l) || it->cost == l.cost)
            return true;
    }
    return false;
}
template<size_t N>
        bool is_dominated_by_any(const deque< Label<N> > & llist, const Label<N> & l)
{
    return is_dominated_by_any(llist, l, Dominates<N>());
}

template<size_t N, typename Comp>
vector<Path> martins(int start_node, int dest_node, Graph & g, int start_time, int day, std::vector<float Edge::*> objectives, Comp std_comp)
{
    std::cout << "Running martins from " << start_node << " to " << dest_node
        << ". Total nodes: " << num_vertices(g.g) << ", total edges: " << num_edges(g.g) << std::endl;
    vector< deque< Label<N> > > P(num_vertices(g.g));
    typename my_queue<N>::Type Q;

    Label<N> start;
    start.node = start_node;
    start.pred = start_node;
    for(size_t i=0; i<N; i++)
        start.cost[i] = 0;
    start.cost[0] = start_time;
    Q.insert(start);
    const typename my_queue<N>::by_cost cost_q_it = Q.get<0>();
    const typename my_queue<N>::by_nodes node_q = Q.get<1>();

    while( !Q.empty() )
    {
        Label<N> l = *(cost_q_it.begin());
        Q.erase(cost_q_it.begin());
        P[l.node].push_back(l);
        graph_traits<Graph_t>::out_edge_iterator ei, end;
        tie(ei,end) = out_edges(l.node, g.g);
        for(; ei != end; ei++)
        {
            Label<N> l2;
            l2.pred = l.node;
            l2.node = boost::target(*ei,g.g);
            l2.pred_idx = P[l.node].size() - 1;

            try{
                l2.cost[0] = g.g[*ei].duration(l.cost[0], day);
                for(size_t i=1; i < N; i++)
                    l2.cost[i] = l.cost[i] + g.g[*ei].*objectives[i-1];

                if(!is_dominated_by_any(Q, l2, std_comp) && !is_dominated_by_any(P[l2.node],l2, std_comp) && (dest_node == invalid_node || !is_dominated_by_any(P[dest_node],l2, std_comp)))
                {
                    typename my_queue<N>::nodes_it it, end;
                    tie(it, end) = node_q.equal_range(l2.node);
                    while(it != end)
                    {
                        if(std_comp(l2, *it))
                            it = Q.get<1>().erase(it);
                        else
                        {
                            it++;
                        }
                    }
                    Q.insert(l2);
                }
            }
            catch(No_traffic)
            {
            }
        }
    }

    vector<Path> ret;
    if(dest_node != invalid_node)
    {
        typename deque< Label<N> >::const_iterator it;
        for(it = P[dest_node].begin(); it != P[dest_node].end(); it++)
        {
            Path p;
            p.cost.push_back(it->cost[0] - start_time);
            if(N >=2)
                p.cost.push_back(it->cost[1]);
            if(N >= 3)
                p.cost.push_back(it->cost[2]);
            if(N >= 4)
                p.cost.push_back(it->cost[3]);
            Label<N> last = *it;
            p.nodes.push_front(last.node);
            while(last.node != start.node)
            {
                last = P[last.pred][last.pred_idx];
                p.nodes.push_front(last.node);
            }
            ret.push_back(p);
        }
    }
    return ret;
}


#endif // MARTINS_IMPL_H
