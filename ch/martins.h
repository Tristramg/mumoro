#include "graph.h"

#include <iostream>
#include <string>
#include <fstream>
#include <deque>
#include <boost/multi_index_container.hpp>
#include <boost/multi_index/ordered_index.hpp>
#include "boost/multi_index/hashed_index.hpp"
#include <boost/multi_index/member.hpp>
#include <boost/array.hpp>

#ifndef MARTINS_H
#define MARTINS_H

using namespace boost::multi_index;
using namespace boost;

float delta(float a, float b);

template<int N>
struct SimpleLabel
{
    typename Graph<N>::node_t node;
    array<float, N> cost;

    bool operator==(const SimpleLabel & l)
    {
        return cost == l.cost;
    }

    bool operator<(const SimpleLabel & l)
    {
        return cost < l.cost;
    }
};

// Retourne vrai si a domine b (ou est équivalent)
template<int N>
bool dominates(boost::array<float, N> a, boost::array<float, N> b)
{
    for(int i=0; i < N; i++)
    {
        if(a[i] > b[i])
            return true;
    }
    //Si on veut qu'il y ait au moins un i tel que a[i] < b[i] 
    return a != b;
}



template<int N>
        struct my_queue
{

    typedef multi_index_container<
            SimpleLabel<N>,
            indexed_by<
            ordered_non_unique<member<SimpleLabel<N>, array<float, N>, &SimpleLabel<N>::cost> >,
            hashed_non_unique<member<SimpleLabel<N>, typename Graph<N>::node_t, &SimpleLabel<N>::node > >
            >
            > Type;

    typedef typename nth_index<Type, 0>::type& by_cost;
    typedef typename nth_index<Type, 1>::type& by_nodes;
    typedef typename nth_index<Type, 1>::type::iterator nodes_it;
};

template<int N>
bool is_dominated_by_any(const typename my_queue<N>::Type & Q, const SimpleLabel<N> & l)
{
    BOOST_FOREACH(SimpleLabel<N> a,  Q.get<1>().equal_range(l.node) )
    {
        if( dominates<N>(a.cost, l.cost) || a.cost == l.cost)
            return true;
    }
    return false;
}

//Algo de martins simplifié pour trouver des "Witness", c'est à dire un chemin qui domine
// le potentiel raccourci
// Comme on ne s'intéresse au chemin, mais juste à l'existence, on ne s'embarasse pas à garder le prédecesseur
template<int N>
bool witness_martins(typename Graph<N>::node_t start_node, typename Graph<N>::node_t dest_node, const typename Graph<N>::Type & g, array<float,N> cost)
{
    typename my_queue<N>::Type Q;

    SimpleLabel<N> start;
    start.node = start_node;
    for(int i=0; i<N; i++)
        start.cost[i] = 0;

    Q.insert(start);
    const typename my_queue<N>::by_cost cost_q_it = Q.get<0>();
    const typename my_queue<N>::by_nodes node_q = Q.get<1>();

    while( !Q.empty() )
    {
        SimpleLabel<N> l = *(cost_q_it.begin());
        Q.erase(cost_q_it.begin());

        BOOST_FOREACH(typename Graph<N>::edge_t e, out_edges(l.node, g))
        {
            SimpleLabel<N> l2;
            l2.node = boost::target(e, g);

            for(int i=0; i < N; i++)
                l2.cost[i] = l.cost[i] + g[e].cost[i];

            if(l2.node == dest_node && dominates<N>(l2.cost, cost))
                return true;

            if(!is_dominated_by_any<N>(Q, l2) && !dominates<N>(cost, l2.cost))
            {
                typename my_queue<N>::nodes_it it, end;
                tie(it, end) = node_q.equal_range(l2.node);
                while(it != end)
                {
                    if(dominates<N>(l2.cost, it->cost))
                        it = Q.get<1>().erase(it);
                    else
                    {
                        it++;
                    }
                }
                Q.insert(l2);
            }
        }
    }

    return false;
}

#endif // MARTINS_H
