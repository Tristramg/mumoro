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

#include <list>
#include <expat.h>
#include <boost/tuple/tuple.hpp>
#include <string>
#include <iostream>
#include <map>
#include <ext/hash_map>
#include <tr1/functional_hash.h>
#include <cstring>
#include <bitset>
#include <iomanip>
#include <sqlite3.h>
#include <sstream>
#ifndef _MAIN_H
#define	_MAIN_H

typedef enum{SET, AND, OR} Operator;
const unsigned short Foot = 0x01, Bike = 0x02, Car = 0x04, Oneway = 0x08, Opposite_bike = 0x16;
class Direction_modifier
{
    std::bitset<5> m_mask;
    Operator m_op;
    public:
    Direction_modifier(Operator, int);
    Direction_modifier();
    void operator()(std::bitset<5> &);
};

struct Node
{
    double lon;
    double lat;
    ushort uses;
    bool inserted;

    Node() : lon(0), lat(0), uses(0), inserted(false) {};

    Node(double _lon, double _lat) :
        lon(_lon), lat(_lat), uses(0), inserted(false)
    {};
};

typedef __gnu_cxx::hash_map<uint64_t, Node, std::tr1::hash<uint64_t> > NodeMapType;

struct Parse_data
{
    uint64_t source_id;
    uint64_t prev_id;
    Node * source;
    Node * prev;
    std::stringstream geom;
    NodeMapType nodes;
    uint64_t ways_count;
    int link_length;
    uint64_t ways_progress;
    std::bitset<5> directions;
    std::list<boost::tuple<uint64_t, uint64_t, Node*, Node*, std::string, double> > links;
    std::map<std::string, std::map<std::string, Direction_modifier> > dir_modifiers ;
    double length;
    double prev_lon;
    double prev_lat;
    sqlite3 *db;
    sqlite3_stmt *stmt;
};

#endif	/* _MAIN_H */

