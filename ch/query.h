// Effectue la requète de calcul d'itinéraire multiobjectif de point à point
// Recherche bidirectionnelle dans un graphe type Contraction Hierarchies
// Ref : Geisberger
//

#include "graph.h"

#include <boost/multi_index_container.hpp>
#include <boost/multi_index/ordered_index.hpp>
#include <boost/multi_index/hashed_index.hpp>
#include <boost/multi_index/member.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/foreach.hpp>


#ifndef QUERY_H
#define QUERY_H


// Décrit un chemin élémentaire
template<int N>
struct Path
{
    boost::array<float, N> cost;
    std::deque<typename Graph<N>::Node> nodes;
};

// Décrit une étiquette (label) utilisée pendant l'exploration
// Cela représente un état de l'exploration et un chemin possible
template<int N>
struct Label
{
    boost::array<float, N> cost; // coût du chemin
    typename Graph<N>::node_t node; // nœud destination du chemin
    boost::shared_ptr<Label> predecessor;
};


// Étant donné une étiquette, il reconstruit le chemin
// Également insère les nœuds court-circuités
    template<int N>
Path<N> unpack(boost::shared_ptr< Label<N> > label_ptr, const typename Graph<N>::Type & graph)
{
    boost::shared_ptr< Label<N> > nullPtr;
    Path<N> p;
    p.cost = label_ptr->cost;

   while(label_ptr != nullPtr)
    {
        p.nodes.push_front( graph[label_ptr->node] );

        // S'il y a un prédecesseur, on déroule les nœuds court-circuités
        if( label_ptr->predecessor != nullPtr )
        {
            bool b;
            typename Graph<N>::edge_t edge; 
            boost::tie(edge, b) = boost::edge(label_ptr->predecessor->node, label_ptr->node, graph);

            BOOST_ASSERT(b); // On s'assure que l'arc pred->label existe bien

            // Pour tout nœud qui avait été count-circuité
            BOOST_FOREACH(int n, graph[edge].shortcuted)
            {
                p.nodes.push_front(graph[n]);
            }
        }
        label_ptr = label_ptr->predecessor;
    }

   return p;
}

// Calcule les plus courts chemins entre deux nœuds
// Retourne une liste de chemins
    template<int N>
std::list< Path<N> > query(typename Graph<N>::node_t source, typename Graph<N>::node_t target, const typename Graph<N>::Type & graph)
{
    //TODO : implémeter
    std::list< Path<N> > paths;
    return paths;
}

    struct my_queue
    {

        typedef boost::multi_index_container<
            SimpleLabel,
            indexed_by<
                ordered_non_unique<member<SimpleLabel, boost::array<float, N>, &SimpleLabel::cost> >,
            hashed_non_unique<member<SimpleLabel, node_t, &SimpleLabel::node > >
                >
                > Type;

        typedef typename nth_index<Type, 0>::type& by_cost;
        typedef typename nth_index<Type, 1>::type& by_nodes;
        typedef typename nth_index<Type, 1>::type::iterator nodes_it;
    };

        bool is_dominated_by_any(const typename my_queue::Type & Q, const SimpleLabel & l)
        {
            BOOST_FOREACH(SimpleLabel a,  Q.get<1>().equal_range(l.node) )
            {
                if( dominates(a.cost, l.cost) || a.cost == l.cost)
                    return true;
            }
            return false;
        }

    //Algo de martins simplifié pour trouver des "Witness", c'est à dire un chemin qui domine
    // le potentiel raccourci
    // Comme on ne s'intéresse au chemin, mais juste à l'existence, on ne s'embarasse pas à garder le prédecesseur
        bool witness_martins(node_t start_node, node_t dest_node, array<float,N> cost)
        {
            typename my_queue::Type Q;

            SimpleLabel start;
            start.node = start_node;
            for(int i=0; i<N; i++)
                start.cost[i] = 0;

            Q.insert(start);
            const typename my_queue::by_cost cost_q_it = Q.get<0>();
            const typename my_queue::by_nodes node_q = Q.get<1>();

            while( !Q.empty() )
            {
                SimpleLabel l = *(cost_q_it.begin());
                Q.erase(cost_q_it.begin());

                BOOST_FOREACH(edge_t e, out_edges(l.node, graph))
                {
                    SimpleLabel l2;
                    l2.node = boost::target(e, graph);

                    for(int i=0; i < N; i++)
                        l2.cost[i] = l.cost[i] + graph[e].cost[i];

                    if(l2.node == dest_node && dominates(l2.cost, cost))
                        return true;

                    if(!is_dominated_by_any(Q, l2) && !dominates(cost, l2.cost))
                    {
                        typename my_queue::nodes_it it, end;
                        tie(it, end) = node_q.equal_range(l2.node);
                        while(it != end)
                        {
                            if(dominates(l2.cost, it->cost))
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



#endif
