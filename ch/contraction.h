// Effectue l'étape de contraction du graphe
// TODO : réfléchir comment foutre le tout dans une classe au lieu de passer toujours graph en paramètre
// (accessoirement, ça ferait moins de typenames et de <N> qui trainent)
#include <boost/progress.hpp>

#include "graph.h"

#include <boost/property_map/property_map.hpp>
#include <iostream>

#ifndef CONTRACTION_H
#define CONTRACTION_H
#endif
