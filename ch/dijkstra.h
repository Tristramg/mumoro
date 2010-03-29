#include "graph.h"
#include <boost/pending/relaxed_heap.hpp>
#include <boost/graph/two_bit_color_map.hpp>

#ifndef DIJKSTRA_H
#define DIJKSTRA_H

//Simple fonction pour tester si le calcul du plus court chemin fonctionne
//On retourne que la distance pour comparer par rapport à du dijkstra
float query_mono(Graph::node_t start, Graph::node_t dest, const Graph::Type & graph);

#endif
