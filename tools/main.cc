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
#include "cmath"

using namespace std;
using namespace boost;

double rad(double deg)
{
    return deg * M_PIl / 180;
}

double distance(double lon1, double lat1, double lon2, double lat2)
{
    const double r = 6371000;

    return acos( sin( rad(lat1) ) * sin( rad(lat2) ) +
                 cos( rad(lat1) ) * cos( rad(lat2) ) * cos( rad(lon2-lon1 ) )
            ) * r;
}

Direction_modifier::Direction_modifier(Operator op, int mask) :
    m_mask(mask), m_op(op)
{}

Direction_modifier::Direction_modifier() :
    m_mask(0x0), m_op(OR)
{}

char
bool2char(bool b)
{
    return (b?'t':'f');
}

void
Direction_modifier::operator()(bitset<5> & dir)
{
    switch(m_op)
    {
        case AND: dir &= m_mask; break;
        case SET: dir = m_mask; break;
        case OR: dir |= m_mask; break;
    }
}

void
start(void *dat, const char *el, const char **attr)
{

    Parse_data * data = (Parse_data *) dat;
    if (strcmp(el, "node") == 0)
    {
        uint64_t id = 0;
        double lat = 0, lon = 0;
        while (*attr != NULL)
        {
            const char* name = *attr++;
            const char* value = *attr++;

            if (strcmp(name, "id") == 0)
            {
                id = atoll(value);
            }
            else if (strcmp(name, "lat") == 0)
            {
                lat = atof(value);
            }
            else if (strcmp(name, "lon") == 0)
            {
                lon = atof(value);
            }
            data->nodes[id] = Node(lon, lat);
        }
    }

    else if (strcmp(el, "nd") == 0)
    {
        const char* name = *attr++;
        const char* value = *attr++;
        if (strcmp(name, "ref") == 0)
        {
            uint64_t node_id = atoll(value);
            data->nodes[node_id].uses++;
        }
    }

    else if(strcmp(el, "way") == 0)
    {
        data->ways_count++;
    }
}

void
start2(void *dat, const char *el, const char **attr)
{
    Parse_data * data = (Parse_data *) dat;
    if (strcmp(el, "nd") == 0)
    {
        const char* name = *attr++;
        const char* value = *attr++;
        if (strcmp(name, "ref") == 0)
        {
            data->prev_id = atoll(value);
            Node * n = &(data->nodes[data->prev_id]);

            if(data->link_length == 0)
            {
                data->source = n;// data->node_id;
                data->source_id = data->prev_id;
            }
            else
            {
                data->geom << ", ";
                data->length += distance(data->prev_lon, data->prev_lat, n->lon, n->lat);
            }

            data->geom << n->lon << " " << n->lat;
            data->prev_lon = n->lon;
            data->prev_lat = n->lat;
            data->prev = n;
            data->link_length++;

            if(n->uses > 1 && data->link_length > 1)
            {
                data->links.push_back(make_tuple(data->source_id, data->prev_id, data->source, n, data->geom.str(), data->length));
                data->source = n;
                data->source_id = data->prev_id;
                data->length = 0;

                data->geom.str("");
                data->geom << n->lon << " " << n->lat;
                data->link_length = 1;
            }
        }
    }
    
    else if(strcmp(el, "tag") == 0)
    {
        string key;
        while (*attr != NULL)
        {
            const char* name = *attr++;
            const char* value = *attr++;

            if ( strcmp(name, "k") == 0 )
                key = value;
            else if ( strcmp(name, "v") == 0 )
            {
                data->dir_modifiers[key][value](data->directions);
            }
        }
    }

}

    void
end(void *data, const char *el)
{
}

    void
end2(void *dat, const char *el)
{
    Parse_data * data = (Parse_data * ) dat;
    if(strcmp(el, "way") == 0)
    {
        int advance = (data->ways_progress++ * 50 / (data->ways_count));
        cout << "\r[" << setfill('=') << setw(advance) << ">" <<setfill(' ') << setw(51-advance) << "]" << flush;
        if(data->link_length >= 2)       
        {
            data->links.push_back(make_tuple(data->source_id, data->prev_id, data->source, data->prev, data->geom.str(), data->length));
        }

        if(data->directions != 0x0)
        {
            list<tuple<uint64_t, uint64_t, Node*, Node*, string, double> >::iterator it;
            for(it = data->links.begin(); it != data->links.end(); it++)
            {
                get<2>(*it)->inserted = true;
                get<3>(*it)->inserted = true;
                sqlite3_bind_int64(data->stmt, 1, get<0>(*it));
                sqlite3_bind_int64(data->stmt, 2, get<1>(*it));
                sqlite3_bind_text(data->stmt, 3, get<4>(*it).c_str(), -1, SQLITE_STATIC);
                sqlite3_bind_int(data->stmt, 4, data->directions.test(1));
                sqlite3_bind_int(data->stmt, 5, (!data->directions.test(3) || data->directions.test(4)));
                sqlite3_bind_int(data->stmt, 6, (data->directions.test(2)));
                sqlite3_bind_int(data->stmt, 7, (!data->directions.test(3)));
                sqlite3_bind_int(data->stmt, 8, (data->directions.test(0)));
                sqlite3_bind_double(data->stmt, 9, get<5>(*it));
                if(sqlite3_step(data->stmt) != SQLITE_DONE)
                {
                    std::cerr << "Unable to insert link "
                        << "Error " << sqlite3_errcode(data->db) << ": " << sqlite3_errmsg(data->db) << std::endl;
                    exit(EXIT_FAILURE);
                }
                sqlite3_reset(data->stmt);
            }
        }
        data->links.clear();
        data->length = 0;
        data->geom.str("");
        data->link_length = 0;
        data->directions = 0x0;
    }

}

    int
main(int argc, char** argv)
{
    if (argc != 3)
    {
        cout << "Usage : " << argv[0] << " in_database.osm out_database" << endl;
        return (EXIT_FAILURE);
    }
    bool add_nodes = true;

    Parse_data data;
    data.directions = 0x00;
    sqlite3_open(argv[2], &data.db);

    sqlite3_exec(data.db, "DROP TABLE nodes", NULL, NULL, NULL);
    sqlite3_exec(data.db, "DROP TABLE links", NULL, NULL, NULL);
    sqlite3_exec(data.db, "CREATE TABLE links(id int primary key, source int, target int, geom text, bike bool, bike_r bool, car bool, car_r bool, foot bool, length double)", NULL, NULL, NULL);
    sqlite3_exec(data.db, "CREATE TABLE nodes(id int primary key, lon double, lat double)", NULL, NULL, NULL);

    // Accessible à tous
    const unsigned short Forall = Bike + Foot + Car;
    data.dir_modifiers["highway"]["primary"] = Direction_modifier(OR, Forall); // 111111
    data.dir_modifiers["highway"]["primary_link"] = Direction_modifier(OR,Forall); // 111111
    data.dir_modifiers["highway"]["secondary"] = Direction_modifier(OR,Forall); // 111111
    data.dir_modifiers["highway"]["tertiary"] = Direction_modifier(OR,Forall); // 111111
    data.dir_modifiers["highway"]["unclassified"] = Direction_modifier(OR,Forall); // 111111
    data.dir_modifiers["highway"]["residential"] = Direction_modifier(OR,Forall); // 111111
    data.dir_modifiers["highway"]["living_street"] = Direction_modifier(OR,Forall); // 111111
    data.dir_modifiers["highway"]["road"] = Direction_modifier(OR,Forall); // 111111
    data.dir_modifiers["highway"]["service"] = Direction_modifier(OR,Forall); // 111111
    data.dir_modifiers["highway"]["track"] = Direction_modifier(OR,Forall); // 111111

    // Accessible qu'aux voitures
    data.dir_modifiers["highway"]["motorway"] = Direction_modifier(OR,Car); // 11000
    data.dir_modifiers["highway"]["trunk"] = Direction_modifier(OR,Car); // 11000
    data.dir_modifiers["highway"]["trunk_link"] = Direction_modifier(OR,Car); // 11000
    data.dir_modifiers["highway"]["motorway_link"] = Direction_modifier(OR,Car); // 11000

    // Accessible qu'aux piétons et cyclistes
    data.dir_modifiers["highway"]["path"] = Direction_modifier(OR, Bike + Car); // 00111

    // Accessible qu'au piétons
    data.dir_modifiers["highway"]["pedestrian"] = Direction_modifier(OR,Foot); // 00001
    data.dir_modifiers["highway"]["footway"] = Direction_modifier(OR,Foot); // 00001
    // Accessible aussi aux piétons
    data.dir_modifiers["highway"]["steps"] = Direction_modifier(OR,Foot); // 00001
    data.dir_modifiers["pedestrians"]["yes"] = Direction_modifier(OR,Foot);
    data.dir_modifiers["foot"]["yes"] = Direction_modifier(OR,Foot);
    data.dir_modifiers["foot"]["designated"] =  Direction_modifier(OR,Foot);


    // Accessible qu'au cyclistes
    data.dir_modifiers["highway"]["cycleway"] = Direction_modifier(OR,Bike); // 00110
    // Accessible aussi aux cylistes
    data.dir_modifiers["cycleway"]["lane"] = Direction_modifier(OR,Bike);
    data.dir_modifiers["cycleway"]["track"] = Direction_modifier(OR,Bike);
    data.dir_modifiers["cycleway"]["share_busway"] = Direction_modifier(OR,Bike);
    data.dir_modifiers["cycleway"]["yes"] = Direction_modifier(OR,Bike);
    data.dir_modifiers["cycle"]["yes"] = Direction_modifier(OR,Bike);
    data.dir_modifiers["busway"]["yes"] = Direction_modifier(OR,Bike);
    data.dir_modifiers["busway"]["track"] = Direction_modifier(OR,Bike);
    // Vélos accessibles en contre-sens
    data.dir_modifiers["cycleway"]["oposite_lane"] = Direction_modifier(OR,Opposite_bike); // 00010
    data.dir_modifiers["cycleway"]["oposite"] = Direction_modifier(OR,Opposite_bike); // 00010
    data.dir_modifiers["cycleway"]["oposite_track"] = Direction_modifier(OR,Opposite_bike); // 00010
    data.dir_modifiers["busway"]["oposite_lane"] = Direction_modifier(OR,Opposite_bike); // 00010

    // Modificateurs qui rendent sens unique
    data.dir_modifiers["junction"]["roundabout"] = Direction_modifier(OR,Oneway); //10101
    data.dir_modifiers["oneway"]["yes"] = Direction_modifier(OR,Oneway); //10101
    data.dir_modifiers["oneway"]["true"] = Direction_modifier(OR,Oneway); //10101

    data.ways_count = 0;
    //==================== STEP 1 =======================//
    cout << "Step 1: reading the xml file, extracting the Nodes list" << flush;

    FILE* fp = fopen(argv[1], "rb");
    XML_Parser parser = XML_ParserCreate(NULL);
    XML_SetElementHandler(parser, start, end);
    XML_SetUserData(parser, &data);
    int done;
    do // loop over whole file content
    {
        char buf[BUFSIZ];
        size_t len = fread(buf, 1, sizeof (buf), fp); // read chunk of data
        done = len < sizeof (buf); // end of file reached if buffer not completely filled
        if (!XML_Parse(parser, buf, (int) len, done))
        {
            // a parse error occured:
            std::cerr << XML_ErrorString(XML_GetErrorCode(parser)) <<
                    " at line " <<
                    XML_GetCurrentLineNumber(parser) << std::endl;
            fclose(fp);
            done = 1;
        }
    }
    while (!done);
    cout << "... DONE !" << endl;
    cout << "    Nodes found: " << data.nodes.size() << endl;
    cout << "    Ways found: " << data.ways_count << endl << endl;


        //===================== STEP 2 ==========================//
    cout << "Step 2: building links and inserting in the database" << endl;
    rewind(fp);
    XML_Parser parser2 = XML_ParserCreate(NULL);
    XML_SetElementHandler(parser2, start2, end2);
    XML_SetUserData(parser2, &data);

    if(sqlite3_prepare_v2(data.db,
                "INSERT INTO links(source, target, geom, bike, bike_r, car, car_r, foot, length) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                -1,
                &data.stmt,
                NULL))
    {
        std::cerr << "Unable to prepare link insert statement. "
            << "Error: " << sqlite3_errmsg(data.db) << std::endl;
        exit(EXIT_FAILURE);
    }
    sqlite3_exec(data.db, "BEGIN TRANSACTION", NULL, NULL, NULL);
    data.link_length = 0;
    data.ways_progress = 0;
    do // loop over whole file content
    {
        char buf[BUFSIZ];
        size_t len = fread(buf, 1, sizeof (buf), fp); // read chunk of data
        done = len < sizeof (buf); // end of file reached if buffer not completely filled
        if (!XML_Parse(parser2, buf, (int) len, done))
        {
            // a parse error occured:
            std::cerr << XML_ErrorString(XML_GetErrorCode(parser)) <<
                    " at line " <<
                    XML_GetCurrentLineNumber(parser) << std::endl;
            fclose(fp);
            done = 1;
        }
    }
    while (!done);
    sqlite3_exec(data.db, "COMMIT TRANSACTION", NULL, NULL, NULL);
    sqlite3_finalize(data.stmt);
    cout << endl << endl;
    //==================== STEP 3 =======================//

    cout << "Step 3: storing the intersection nodes in the database" << endl;

    if(add_nodes)
    {
        sqlite3_exec(data.db, "BEGIN TRANSACTION", NULL, NULL, NULL);
        if(sqlite3_prepare_v2(data.db,
                    "INSERT INTO nodes(id, lon, lat) VALUES(?,?,?)",
                    -1,
                    &data.stmt,
                    NULL))
        {
            std::cerr << "Unable to prepare node insert statement. "
                << "Error: " << sqlite3_errmsg(data.db) << std::endl;
            exit(EXIT_FAILURE);
        }
        uint64_t count = 0, step = data.nodes.size() / 50, next_step = 0;

        for(NodeMapType::const_iterator i = data.nodes.begin(); i != data.nodes.end(); i++)
        {
            count++;
            if(count >= next_step)
            {
                int advance = (count * 50 / (data.nodes.size()));
                cout << "\r[" << setfill('=') << setw(advance) << ">" <<setfill(' ') << setw(51-advance) << "]" << flush;
                next_step += step;
            }
            if((*i).second.inserted && (*i).second.uses > 1)
            {
                sqlite3_bind_int64(data.stmt, 1, (*i).first);
                sqlite3_bind_double(data.stmt, 2, (*i).second.lon);
                sqlite3_bind_double(data.stmt, 3, (*i).second.lat);
                if(sqlite3_step(data.stmt) != SQLITE_DONE)
                {
                    std::cerr << "Unable to insert node. "
                        << "Error " << sqlite3_errcode(data.db) << ": " << sqlite3_errmsg(data.db) << std::endl;
                    exit(EXIT_FAILURE);
                }
                sqlite3_reset(data.stmt);

            }
        }
        sqlite3_finalize(data.stmt);
        sqlite3_exec(data.db, "COMMIT TRANSACTION", NULL, NULL, NULL);
        cout << " DONE!" << endl << endl;
    }
    else
        cout << "  Skiped" << endl;

sqlite3_close(data.db);
    return (EXIT_SUCCESS);
}

