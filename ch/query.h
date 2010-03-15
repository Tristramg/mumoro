// Effectue la requète de calcul d'itinéraire multiobjectif de point à point
// Recherche bidirectionnelle dans un graphe type Contraction Hierarchies
// Ref : Geisberger
//

#include "graph.h"

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

#endif
