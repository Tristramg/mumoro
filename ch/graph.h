// Définit les structures de données pour un graphe
// permettant un calcul d'itinéraire multiobjectif
//

#include <boost/graph/adjacency_list.hpp>
#include <boost/array.hpp>
#include <boost/graph/adj_list_serialize.hpp>
#include <boost/serialization/list.hpp>

#include <deque>

#ifndef GRAPH_H
#define GRAPH_H

// La structure est templatée en fonction du nombre d'objectifs
template<int N>
struct Graph
{

    struct Node
    {
        static const int undefined = -1;
        int order; // Définit l'ordre du nœud dans le graphe
        int id; // Identifiant orginal
        int priority; // Valeur de l'heuristique TODO: penser à le foutre à l'extérieur de la map...

        Node() : order(undefined) {} // Par défaut, l'ordre du nœud est indéfini
            friend class boost::serialization::access;
        template<class Archive>
            void serialize(Archive& ar, const unsigned int version){
                    ar & order & id & priority;
                }
    };

    struct Edge
    {
        float cost0;
        boost::array<float, N> cost; // Coût multiobjectif de l'arc
        std::list<int> shortcuted; // Nœuds court-circuités par cet arc. La liste est vide si c'est un arc original
            friend class boost::serialization::access;
        template<class Archive>
            void serialize(Archive& ar, const unsigned int version){
                    ar & cost & shortcuted;
                }
    };

    //NOTE: comme on modifie à tours de bras les arcs, il est important que les arcs soient
    //stockés dans une liste (problème de perfs et d'invalidation d'itérateurs)
    // (c'est le premier paramètre du template)
    typedef boost::adjacency_list<boost::listS, boost::vecS, boost::bidirectionalS, Node, Edge > Type;
    typedef typename boost::graph_traits<Type>::edge_descriptor edge_t;
    typedef typename boost::graph_traits<Type>::vertex_descriptor node_t;
};

#endif
