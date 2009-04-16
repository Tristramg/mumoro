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
#include <stdlib.h>
#include <iostream>
#include "fcgi_stdio.h" 
#include "curl/curl.h"  
#include <boost/regex.hpp>
#include <map>
#include "../../lib/shortest_path.h"

#include <boost/algorithm/string.hpp>
#include <boost/algorithm/string/split.hpp>
using namespace boost;
using namespace std;
using namespace Mumoro;

struct Geomatch_fail{};

// This is the writer call back function used by curl  
static int writer(char *data, size_t size, size_t nmemb,  
        std::string *buffer)  
{  
    // What we will return  
    int result = 0;  
    buffer->clear();

    if (buffer != NULL)  
    {  
        // Append the data to the buffer  
        buffer->append(data, size * nmemb);  

        // How much did we write?  
        result = size * nmemb;  
    }  

    return result;  
}  

std::pair<float,float> match(const std::string & address)
{
    string no_space = address;
    for(string::iterator it = no_space.begin(); it != no_space.end(); it++)
    {
        if( *it == ' ' )
            *it = '+';
    }
    string url = "http://local.yahooapis.com/MapsService/V1/geocode?appid=rCs0LXLV34F_z..kemAky2NUloU3ocCvsXep0pcKmQhWgLY2bucI0p0sumv1f8sjTGX34D2bBJKEhg--&location=";
    url += no_space;
    CURL *curl;  
    CURLcode result;  
    curl = curl_easy_init();  
    string buffer;

    if (curl)  
    {  
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());  
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writer);  
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &buffer);  

        // Attempt to retrieve the remote page  
        result = curl_easy_perform(curl);  

        // Always cleanup  
        curl_easy_cleanup(curl);  

        // Did we succeed?  
        float lon, lat;
        if (result == CURLE_OK)  
        {  
            boost::regex lat_e(".*<Latitude>(.*)</Latitude>.*");
            boost::regex lon_e(".*<Longitude>(.*)</Longitude>.*");
            boost::smatch what;
            if(boost::regex_match(buffer, what, lon_e))
                lon = boost::lexical_cast<float>(what[1]);
            else
            {
                cout << "Lon failed" << endl;
                throw Geomatch_fail();
            }

            if(boost::regex_match(buffer, what, lat_e))
                lat = boost::lexical_cast<float>(what[1]);
            else
            {
                cout << "Lat failed" << endl;
                throw Geomatch_fail();
            }
        }  
        else  
        {  
            cout << "Curl failed" << endl;
            throw Geomatch_fail();
        }  
        return make_pair(lon, lat);
    }  
    return make_pair(0,0);
}

Shortest_path p;

std::map<string,string> parse(const std::string & s)
{
    vector<string> SplitVec; // #2: Search for tokens
    split( SplitVec, s, is_any_of("&") );
    map<string,string> ret_map;

    for(vector<string>::const_iterator it = SplitVec.begin(); it != SplitVec.end(); it++)
    {
        regex ad("(.*)=(.*)");
        smatch what;
        if(boost::regex_match((*it), what, ad))
        {
            ret_map[what[1]] = what[2];
        }
    }

    return ret_map;
}

string un_escape(const string & s)
{
    string ret;
    string::const_iterator it;
    for(it = s.begin(); it != s.end(); it++)
    {
        if( (*it) != '%')
            ret += (*it);
        else
        {
            
            ret += lexical_cast<int>(*++it) * 16 + lexical_cast<int>(*++it);
        }
    }
    return ret;
}

int main(int argc, char ** argv)
{


    Layer foot = p.add_layer("/home/tristram/mumoro/toulouse.mum", Foot, false);
    Layer sub = p.add_layer("/home/tristram/mumoro/toulouse.mum", Subway, false);
    Layer velouse = p.add_layer("/home/tristram/mumoro/toulouse.mum", Bike, false);

    p.connect(foot, sub, FunctionPtr(new Const_cost(200)),  FunctionPtr( new Const_cost(60) ),"/home/tristram/mumoro/toulouse.mum", "metroA" );
    p.connect(foot, velouse, FunctionPtr(new Const_cost(60)),  FunctionPtr( new Const_cost(30) ),"/home/tristram/mumoro/toulouse.mum", "velouse" );

    p.build();

    while(FCGI_Accept() >= 0)
    {
        printf("Content-type: text/xml\r\n"
                "\r\n");
        char * query_string = getenv("QUERY_STRING");

        map<string,string> query_map = parse(un_escape(query_string));

        map<string,string>::iterator it = query_map.begin();
        for( ; it != query_map.end(); it ++)
            cout << (*it).first << " = " << (*it).second << "\n" << endl;

        string error = "<error>\n";
        Node start, dest;
        bool fail = false;
        if(query_map.find("start") != query_map.end())
        {
            cout << query_map["start"] << endl;
            try
            {
                pair<float, float> coord = match(query_map["start"]);
                start = p.match(coord.first, coord.second);
            }
            catch(...)
            {
                error += "<parsing>start</parsing>\n";
                fail = true;
            }
        }
        else
        {
            error += "<input>start</input>\n";
            fail = true;
        }

        if(query_map.find("dest") != query_map.end())
        {
            cout << query_map["dest"] << endl;
            try
            {
                pair<float, float> coord = match(query_map["dest"]);
                dest = p.match(coord.first, coord.second);
            }
            catch(...)
            {
                error += "<parsing>dest</parsing>\n";
                fail = true;
            }
        }
        else
        {
            error += "<input>dest</input>\n";
            fail = true;
        }

        if(!fail)
        {
            cout << "trying to compute " << start.id << " " << dest.id << endl;
            try
            {
                std::string xml = p.compute_xml(start.id, dest.id);
                cout << "failed" << endl;
                printf("%s", xml.c_str());

            }
            catch(...)
            {
                error += "<computing></computing>\n";
                fail = true;
            }
        }

        if(fail)
        {
            error += "</error>";
            printf("%s", error.c_str());
        }

    }

    return 0;

}
