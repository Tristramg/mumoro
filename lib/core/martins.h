#ifndef MARTINS_H
#define MARTINS_H

#include "graph_wrapper.h"

enum Objective {dist, elevation, mode_change, cost, line_change, co2};

struct Path
{
    std::vector<float> cost;
    std::list<int> nodes;
    size_t size() const
    {
        return nodes.size();
    }
};

std::vector<Path> martins(int start, int dest, Graph & g, int start_time = 30000);
std::vector<Path> martins(int start, int dest, Graph & g, int start_time, Objective);
std::vector<Path> martins(int start, int dest, Graph & g, int start_time, Objective, Objective);
std::vector<Path> martins(int start, int dest, Graph & g, int start_time, Objective, Objective, Objective);

std::vector<Path> relaxed_martins(int start, int dest, Graph & g, int start_time, Objective o1, float r1);

std::vector<Path> relaxed_martins(int start, int dest, Graph & g, int start_time, Objective o1, float r1, Objective o2, float r2);

std::vector<Path> relaxed_martins(int start, int dest, Graph & g, int start_time, Objective o1, float r1, Objective o2, float r2, Objective o3, float r3);
#endif // MARTINS_H
