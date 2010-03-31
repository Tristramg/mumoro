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
#include <deque>

#ifndef QUERY_H
#define QUERY_H

//On définit diverses structures utilisées pour l'algo de martins

// Décrit un chemin élémentaire
struct Path
{
    Graph::cost_t cost;
    std::deque<Graph::node_t> nodes;
};


std::list<Path> query(Graph::node_t source, Graph::node_t target, const Graph::Type & graph);

bool martins(Graph::node_t start_node, Graph::node_t dest_node, const Graph & g);
bool ch_martins(Graph::node_t start_node, Graph::node_t dest_node, const Graph & g);
bool martins_witness(Graph::node_t start_node, Graph::node_t dest_node, Graph::cost_t cost, const Graph::Type & g);
#endif
