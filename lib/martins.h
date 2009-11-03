#ifndef MARTINS_H
#define MARTINS_H

#include "MultimodalGraph.h"


struct Path
{
    std::vector<float> cost;
    std::list<Node> nodes;
    size_t size() const
    {
        return nodes.size();
    }
};

std::vector<Path> martins(node_t start, node_t dest, MultimodalGraph & g, int start_time = 30000);
std::vector<Path> martins(node_t start, node_t dest, MultimodalGraph & g, float Edge::*, int start_time = 30000);
std::vector<Path> martins(node_t start, node_t dest, MultimodalGraph & g, float Edge::*, float Edge::*, int start_time = 30000);
std::vector<Path> relaxed_martins(node_t start, node_t dest, MultimodalGraph & g, float Edge::*, float Edge::*,  int start_time = 30000);
std::vector<Path> martins(node_t start, node_t dest, MultimodalGraph & g, float Edge::*, float Edge::*, float Edge::*, int start_time = 30000);

#endif // MARTINS_H
