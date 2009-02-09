/*
    This file is part of Mumoro.

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
*/

#include "graph.h"

#include <list>
#include <stdlib.h>
#include <iostream>
#include <map>
#include "boost/date_time/posix_time/posix_time.hpp"

#include "sqlite3.h"
#ifndef _SHORTESTPATH_H
#define _SHORTESTPATH_H

namespace Mumoro
{
    /** Describes a step in a path
     * 
     * It is usualy an arc in the network (between two consecutive bus stops
     * or between to road crosses). However it can also be a transport mode
     * switching. Therefore source and target nodes can be identical.
     */
    struct Path_elt
    {
        Node source; /**< Source node */
        Node target; /**< Target node */
        double length; /**< Length in meters (0 if it is mode switching) */
        double duration; /**< Duration in seconds */
        Transport_mode mode; /**< Transport mode used on that link */
    };

    class Layer
    {
        int offset;
        int count;
        std::vector<std::pair<double, double> > coord;
        public:
        std::map<uint64_t, int> nodes_map;
        Layer(int=0);
        int add_node(uint64_t, double, double);
        int match(double lon, double lat);
        Node get(int) const;
        int cnt() { return count; }
    };

    /** Exception thrown when asking for a non existing node */
    struct Node_not_found {}; 

    /** Exception thrown when no path is found */
    struct Path_not_found {};

    const double foot_speed = 1; /**< in m/s, almost 4km/h */
    const double bike_speed = 4; /**< in m/s, arround 15km/h */
    const double car_speed = 8; /**< in m/s, arround 30km/h */
    const double subway_speed = 12;

    bool add_direct(sqlite3_stmt *, Transport_mode);
    bool add_reverse(sqlite3_stmt *, Transport_mode);
    FunctionPtr direct_cost(sqlite3_stmt *, Transport_mode);
    FunctionPtr reverse_coust(sqlite3_stmt *, Transport_mode);
    /**
     * Classe permettant de calculer à proprement parler le plus court chemin
     */
    class Shortest_path
    {
        CGraph cg; /**< Graphe qui est généré à la construction de l'instance */
        
        std::vector<Layer> layers;
        std::vector<Edge_property> edge_prop;
        /**
         * Initialise le graphe
         */
        int offset();

        public:
        void build();

        /** Finds the closest node to the given coordiantes
         *
         * \throw Node_not_found()
         * If no node is found within a certain radius
         */
        Node match(double lon, double lat);

        Layer add_layer(const char * db, Transport_mode mode, bool acessible);

        void connect(Layer &, Layer &, FunctionPtr, FunctionPtr, const std::string, const std::string); 


        /** Calculates the shortest path between start and end at a given time
         *
         * Returns a list of path elements
         */
        std::list<Path_elt> compute(cvertex start_idx, cvertex end_idx, int start_time = 3600);
    };
}

#endif	/* _SHORTESTPATH_H */

