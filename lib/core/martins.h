/*    This file is part of Mumoro.

    Mumoro is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Mumoro is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Mumoro.  If not, see <http://www.gnu.org/licenses/>.

    © Université de Toulouse 1 2010
    Author: Tristram Gräbener*/

#ifndef MARTINS_H
#define MARTINS_H

#include "graph_wrapper.h"

enum Objective {dist, elevation, mode_change, cost, line_change, co2, penibility};

struct Path
{
    std::vector<float> cost;
    std::list<int> nodes;
    size_t size() const
    {
        return nodes.size();
    }
};

std::vector<Path> martins(int start, int dest, Graph & g, int start_time, int day = 30000);
std::vector<Path> martins(int start, int dest, Graph & g, int start_time, int day, Objective);
std::vector<Path> martins(int start, int dest, Graph & g, int start_time, int day, Objective, Objective);
std::vector<Path> martins(int start, int dest, Graph & g, int start_time, int day, Objective, Objective, Objective);

std::vector<Path> relaxed_martins(int start, int dest, Graph & g, int start_time, int day, Objective o1, float r1);

std::vector<Path> relaxed_martins(int start, int dest, Graph & g, int start_time, int day, Objective o1, float r1, Objective o2, float r2);

std::vector<Path> relaxed_martins(int start, int dest, Graph & g, int start_time, int day, Objective o1, float r1, Objective o2, float r2, Objective o3, float r3);
#endif // MARTINS_H
