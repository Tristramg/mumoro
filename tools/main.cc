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

uint64_t prev_id;
Node * source;
Node * prev;
std::stringstream geom;
NodeMapType nodes;
uint64_t ways_count;
int link_length;
uint64_t ways_progress;
std::bitset<6> directions;
std::list<boost::tuple<Node*, Node*, std::string, double> > links;
double length;
sqlite3 *db;
sqlite3_stmt *stmt;
std::map<std::string, std::string> tag;
Dir_params dir_modifiers;
int nodes_inserted;
int links_inserted;

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

    void
start(void *dat, const char *el, const char **attr)
{
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
            nodes[id] = Node(lon, lat, id);
            prev_id = id;
        }
    }

    else if (strcmp(el, "nd") == 0)
    {
        const char* name = *attr++;
        const char* value = *attr++;
        if (strcmp(name, "ref") == 0)
        {
            uint64_t node_id = atoll(value);
            nodes[node_id].uses++;
        }
    }

    else if (strcmp(el, "tag") == 0)
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
                tag[key] = value;
            }
        }
    }

    else if(strcmp(el, "way") == 0)
    {
        ways_count++;
    }
}

    void
start2(void *dat, const char *el, const char **attr)
{
    if (strcmp(el, "nd") == 0)
    {
        const char* name = *attr++;
        const char* value = *attr++;
        if (strcmp(name, "ref") == 0)
        {
            uint64_t id = atoll(value);
            Node * n = &(nodes[id]);

            if(link_length == 0)
            {
                source = n;
            }
            else
            {
                geom << ", ";
                length += distance(prev->lon, prev->lat, n->lon, n->lat);
            }

            geom << n->lon << " " << n->lat;
            prev = n;
            link_length++;

            if(n->uses > 1 && link_length > 1)
            {
                links.push_back(make_tuple(source, n, geom.str(), length));
                source = n;
                length = 0;

                geom.str("");
                geom << n->lon << " " << n->lat;
                link_length = 1;
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
                directions |= dir_modifiers[key][value];
            }
        }
    }

}

    void
end(void *dat, const char *el)
{
    if (strcmp(el, "node") == 0)
    {
        if(tag["railway"] == "station" )
        {
            nodes[prev_id].uses = 2;
        }
        tag.clear();
    }
}

    void
end2(void *dat, const char *el)
{
    if(strcmp(el, "way") == 0)
    {
        int advance = (ways_progress++ * 50 / (ways_count));
        cout << "\r[" << setfill('=') << setw(advance) << ">" <<setfill(' ') << setw(50-advance) << "] " << flush;
        if(link_length >= 2)       
        {
            links.push_back(make_tuple(source, prev, geom.str(), length));
        }

        if(directions != 0)
        {
            list<tuple<Node*, Node*, string, double> >::iterator it;
            for(it = links.begin(); it != links.end(); it++)
            {
                get<0>(*it)->inserted = true;
                get<1>(*it)->inserted = true;
                sqlite3_bind_int64(stmt, 1, get<0>(*it)->id);
                sqlite3_bind_int64(stmt, 2, get<1>(*it)->id);
                sqlite3_bind_text(stmt, 3, get<2>(*it).c_str(), -1, SQLITE_STATIC);
                sqlite3_bind_int(stmt, 4, directions.test(1));
                sqlite3_bind_int(stmt, 5, (!directions.test(3) || directions.test(4)));
                sqlite3_bind_int(stmt, 6, (directions.test(2)));
                sqlite3_bind_int(stmt, 7, (!directions.test(3)));
                sqlite3_bind_int(stmt, 8, (directions.test(0)));
                sqlite3_bind_int(stmt, 9, (directions.test(5)));
                sqlite3_bind_double(stmt, 10, get<3>(*it));
                sqlite3_bind_double(stmt, 11, get<0>(*it)->lon);
                sqlite3_bind_double(stmt, 12, get<0>(*it)->lat);
                sqlite3_bind_double(stmt, 13, get<1>(*it)->lon);
                sqlite3_bind_double(stmt, 14, get<1>(*it)->lat);
                if(sqlite3_step(stmt) != SQLITE_DONE)
                {
                    cerr << "Unable to insert link "
                        << "Error " << sqlite3_errcode(db) << ": " << sqlite3_errmsg(db) << endl;
                    exit(EXIT_FAILURE);
                }
                sqlite3_reset(stmt);
                links_inserted++;
            }
        }
        links.clear();
        length = 0;
        geom.str("");
        link_length = 0;
        directions = 0x0;
    }

}

    int
main(int argc, char** argv)
{
    dir_modifiers = get_dir_params();
    if (argc != 3)
    {
        cout << "Usage: " << argv[0] << " in_database.osm out_database" << endl;
        return (EXIT_FAILURE);
    }

    sqlite3_open(argv[2], &db);

    // We make sure the database is as we want it
    sqlite3_exec(db, "DROP TABLE nodes", NULL, NULL, NULL);
    sqlite3_exec(db, "DROP TABLE links", NULL, NULL, NULL);
    sqlite3_exec(db, "CREATE TABLE links(id int primary key, source int, target int, geom text, bike bool, bike_r bool, car bool, car_r bool, foot bool, subway bool, length double, lon1 double, lat1 double, lon2 double, lat2 double)", NULL, NULL, NULL);
    sqlite3_exec(db, "CREATE TABLE nodes(id int primary key, lon double, lat double)", NULL, NULL, NULL);

    //==================== STEP 1 =======================//
    cout << "Step 1: reading the xml file, extracting the Nodes list" << flush;

    FILE* fp = fopen(argv[1], "rb");
    XML_Parser parser = XML_ParserCreate(NULL);
    XML_SetElementHandler(parser, start, end);
    int done;
    do // loop over whole file content
    {
        char buf[BUFSIZ];
        size_t len = fread(buf, 1, sizeof (buf), fp); // read chunk of data
        done = len < sizeof (buf); // end of file reached if buffer not completely filled
        if (!XML_Parse(parser, buf, (int) len, done))
        {
            // a parse error occured:
            cerr << XML_ErrorString(XML_GetErrorCode(parser)) <<
                " at line " <<
                XML_GetCurrentLineNumber(parser) << endl;
            fclose(fp);
            done = 1;
        }
    }
    while (!done);
    cout << "... DONE!" << endl;
    cout << "    Nodes found: " << nodes.size() << endl;
    cout << "    Ways found: " << ways_count << endl << endl;


    //===================== STEP 2 ==========================//
    cout << "Step 2: building links and inserting in the database" << endl;
    rewind(fp);
    XML_Parser parser2 = XML_ParserCreate(NULL);
    XML_SetElementHandler(parser2, start2, end2);

    if(sqlite3_prepare_v2(db,
                "INSERT INTO links(source, target, geom, bike, bike_r, car, car_r, foot, subway, length, lon1, lat1, lon2, lat2) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                -1,
                &stmt,
                NULL))
    {
        cerr << "Unable to prepare link insert statement. "
            << "Error: " << sqlite3_errmsg(db) << endl;
        exit(EXIT_FAILURE);
    }
    sqlite3_exec(db, "BEGIN TRANSACTION", NULL, NULL, NULL);

    do // loop over whole file content
    {
        char buf[BUFSIZ];
        size_t len = fread(buf, 1, sizeof (buf), fp); // read chunk of data
        done = len < sizeof (buf); // end of file reached if buffer not completely filled
        if (!XML_Parse(parser2, buf, (int) len, done))
        {
            // a parse error occured:
            cerr << XML_ErrorString(XML_GetErrorCode(parser)) <<
                " at line " <<
                XML_GetCurrentLineNumber(parser) << endl;
            fclose(fp);
            done = 1;
        }
    }
    while (!done);
    sqlite3_exec(db, "COMMIT TRANSACTION", NULL, NULL, NULL);
    sqlite3_finalize(stmt);
    cout << "DONE!" << endl << endl;

    //==================== STEP 3 =======================//
    cout << "Step 3: storing the intersection nodes in the database" << endl;

    sqlite3_exec(db, "BEGIN TRANSACTION", NULL, NULL, NULL);
    if(sqlite3_prepare_v2(db,
                "INSERT INTO nodes(id, lon, lat) VALUES(?,?,?)",
                -1,
                &stmt,
                NULL))
    {
        cerr << "Unable to prepare node insert statement. "
            << "Error: " << sqlite3_errmsg(db) << endl;
        exit(EXIT_FAILURE);
    }
    uint64_t count = 0, step = nodes.size() / 50, next_step = 0;

    for(NodeMapType::const_iterator i = nodes.begin(); i != nodes.end(); i++)
    {
        count++;
        if(count >= next_step)
        {
            int advance = (count * 50 / (nodes.size()));
            cout << "\r[" << setfill('=') << setw(advance) << ">" <<setfill(' ') << setw(50-advance) << "] " << flush;
            next_step += step;
        }

        if( (*i).second.inserted )
        {
            sqlite3_bind_int64(stmt, 1, (*i).first);
            sqlite3_bind_double(stmt, 2, (*i).second.lon);
            sqlite3_bind_double(stmt, 3, (*i).second.lat);
            if(sqlite3_step(stmt) != SQLITE_DONE)
            {
                cerr << "Unable to insert node. "
                    << "Error " << sqlite3_errcode(db) << ": " << sqlite3_errmsg(db) << endl;
                exit(EXIT_FAILURE);
            }
            sqlite3_reset(stmt);
            nodes_inserted++;
        }
    }
    sqlite3_finalize(stmt);
    sqlite3_exec(db, "COMMIT TRANSACTION", NULL, NULL, NULL);
    cout << "DONE!" << endl << endl;

    cout << "Nodes in database: " << nodes_inserted << endl;
    cout << "Links in database: " << links_inserted << endl;
    cout << "Happy routing! :)" << endl << endl;
        
    sqlite3_close(db);
    return (EXIT_SUCCESS);
}

