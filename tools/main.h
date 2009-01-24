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
#define _MAIN_H

const unsigned short Foot = 0x01,
      Bike = 0x02,
      Car = 0x04,
      Oneway = 0x08,
      Opposite_bike = 0x16,
      Subway = 0x32;

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


typedef std::map<std::string, std::map<std::string, unsigned short> > Dir_params ;

Dir_params get_dir_params();

#endif /* _MAIN_H */

