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

#include "main.h"

Dir_params get_dir_params()
{
    Dir_params dir_modifiers;

    // Anyone can use it
    const unsigned short Forall = Bike + Foot + Car;
    dir_modifiers["highway"]["primary"] = Forall;
    dir_modifiers["highway"]["primary_link"] = Forall;
    dir_modifiers["highway"]["secondary"] = Forall;
    dir_modifiers["highway"]["tertiary"] = Forall;
    dir_modifiers["highway"]["unclassified"] = Forall;
    dir_modifiers["highway"]["residential"] = Forall;
    dir_modifiers["highway"]["living_street"] = Forall;
    dir_modifiers["highway"]["road"] = Forall;
    dir_modifiers["highway"]["service"] = Forall;
    dir_modifiers["highway"]["track"] = Forall; 

    // Only cars can use it
    dir_modifiers["highway"]["motorway"] = Car;
    dir_modifiers["highway"]["trunk"] = Car;
    dir_modifiers["highway"]["trunk_link"] = Car;
    dir_modifiers["highway"]["motorway_link"] = Car;

    // Only bikes or pedestrians can use it
    dir_modifiers["highway"]["path"] = Bike + Foot;

    // Pedestrians
    dir_modifiers["highway"]["pedestrian"] = Foot;
    dir_modifiers["highway"]["footway"] = Foot;
    dir_modifiers["highway"]["steps"] = Foot; 
    dir_modifiers["pedestrians"]["yes"] = Foot;
    dir_modifiers["foot"]["yes"] = Foot;
    dir_modifiers["foot"]["designated"] = Foot;

    // For bikes
    dir_modifiers["highway"]["cycleway"] = Bike;
    dir_modifiers["cycleway"]["lane"] = Bike;
    dir_modifiers["cycleway"]["track"] = Bike;
    dir_modifiers["cycleway"]["share_busway"] = Bike;
    dir_modifiers["cycleway"]["yes"] = Bike;
    dir_modifiers["cycle"]["yes"] = Bike;
    dir_modifiers["busway"]["yes"] = Bike;
    dir_modifiers["busway"]["track"] = Bike;

    // Bikes don't care about oneway
    dir_modifiers["cycleway"]["oposite_lane"] = Opposite_bike;
    dir_modifiers["cycleway"]["oposite"] = Opposite_bike;
    dir_modifiers["cycleway"]["oposite_track"] = Opposite_bike;
    dir_modifiers["busway"]["oposite_lane"] = Opposite_bike;

    // Oneway
    dir_modifiers["junction"]["roundabout"] = Oneway;
    dir_modifiers["oneway"]["yes"] = Oneway;
    dir_modifiers["oneway"]["true"] = Oneway;

    // It's a subway!
    dir_modifiers["railway"]["subway"] = Subway;

    return dir_modifiers;
}
