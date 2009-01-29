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
    /** Describes a node */
    class Node
    {
        public:
        /** Builds a node from a given id
         *
         * \throw Node_not_found()
         */
        Node(uint64_t id);
        uint64_t id; /**< id of the node */
        double lon; /**< longitude in decimal degrees */
        double lat; /**< latitude in decimal degrees */
    };

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

    /** Exception thrown when asking for a non existing node */
    struct Node_not_found {}; 

    /** Exception thrown when no path is found */
    struct Path_not_found {};


    const double foot_speed = 1; /**< in m/s, almost 4km/h */
    const double bike_speed = 4; /**< in m/s, arround 15km/h */
    const double car_speed = 8; /**< in m/s, arround 30km/h */
    const double subway_speed = 9;

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
        std::map<uint64_t, int> foot_map; /**< Conversion entre les identifiants des nœuds de la base de données et les identifiants renumérotés */
        std::map<int, uint64_t> rev_map;
        int node_count; /**< Nombre total de nœuds dans le graphe */

        sqlite3 * db;

        /**
         * Initialise le graphe
         */
        void init(const char *, Transport_mode m);


        public:

        /** Constructeur
         *
         * str : string de connection vers la base de cartographie
         */
        Shortest_path(const char *, Transport_mode mode = Car);

        /**
         * Destructeur
         */
        ~Shortest_path();

        /** Internaly, nodes are renumbered.
         * This function returns the internal node id, or adds the node
         * into the graph and returns its internal id
         */
        int node_internal_id_or_add( uint64_t node_id);

        /** Internaly, nodes are renumbered.
         * This function returns the internal node id,
         *
         * \throw Node_not_found()
         */
        int node_internal_id(uint64_t node_id);

        /** Finds the closest node to the given coordiantes
         *
         * \throw Node_not_found()
         * If no node is found within a certain radius
         */
        Node match(double lon, double lat);


        /** Returns the number of nodes */
        int nodes() const;

        /** Calculates the shortest path between start and end at a given time
         *
         * Returns a list of path elements
         */
        std::list<Path_elt> compute(uint64_t start, uint64_t end, int start_time = 3600);
    };
}

#endif	/* _SHORTESTPATH_H */

