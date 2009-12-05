#ifndef MARTINS_H
#define MARTINS_H

#include "graph_wrapper.h"

typedef float Edge::*Edge_member;

struct Path
{
    std::vector<float> cost;
    std::list<int> nodes;
    size_t size() const
    {
        return nodes.size();
    }
};

std::vector<Path> martins_py(int start, int dest, Graph & g);
std::vector<Path> martins(int start, int dest, Graph & g, int start_time = 30000);
std::vector<Path> martins(int start, int dest, Graph & g, Edge_member, int start_time = 30000);
std::vector<Path> martins(int start, int dest, Graph & g, float Edge::*, float Edge::*, int start_time = 30000);
std::vector<Path> relaxed_martins(int start, int dest, Graph & g, float Edge::*, float Edge::*,  int start_time = 30000);
std::vector<Path> martins(int start, int dest, Graph & g, float Edge::*, float Edge::*, float Edge::*, int start_time = 30000);

#endif // MARTINS_H
