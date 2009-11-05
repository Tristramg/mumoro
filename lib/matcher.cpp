#include <boost/algorithm/string.hpp>
#include <boost/algorithm/string/split.hpp>
#include <boost/regex.hpp>
#include <boost/lexical_cast.hpp>
#include "fcgi_stdio.h"

#include <pqxx/pqxx>
using namespace std;
std::map<string,string> parse(const std::string & s)
{
    vector<string> SplitVec; // #2: Search for tokens
    boost::split( SplitVec, s, boost::is_any_of("&") );
    map<string,string> ret_map;

    for(vector<string>::const_iterator it = SplitVec.begin(); it != SplitVec.end(); it++)
    {
      boost::regex ad("(.*)=(.*)");
      boost::smatch what;
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
            
            ret += boost::lexical_cast<int>(*++it) * 16 + boost::lexical_cast<int>(*++it);
        }
    }
    return ret;
}

int main(int argc, char ** argv)
{

    pqxx::connection conn ("dbname=mumoro user=tristram");
    while(FCGI_Accept() >= 0)
    {

        pqxx::work sql(conn, "Maptchin closest node");
        printf("Content-type: application/json\r\n\r\n");
        char * query_string = getenv("QUERY_STRING");
        string escaped = un_escape(query_string);
        map<string,string> query_map = parse(escaped);
        std::stringstream output, error_msg;
        bool fail = false;

        if(query_map.find("lon") == query_map.end())
        {
            error_msg << "No longitude defined ";
            fail = true;
        }

        if(query_map.find("lat") == query_map.end())
        {
            error_msg << "No latitude defined";
            fail = true;
        }

        if(fail)
        {
            printf("{\"error\": \"%s\"}\n", error_msg.str().c_str());
        }
        else
        {
            string query = "SELECT id FROM sf_nodes WHERE st_dwithin(the_geom, st_setsrid(st_makepoint("
                + query_map["lon"] + ", "
                + query_map["lat"]
                + "), 4326), 0.001) ORDER BY st_distance(the_geom, st_setsrid(ST_makepoint("
                + query_map["lon"] + ", "
                + query_map["lat"]
                + "), 4326)) LIMIT 1";
            pqxx::result R;
            R = sql.exec(query);
            if(R.size() < 1)
                printf("{\"error\": \"No node found\"}\n");
            else
            {
                uint64_t node;
                R[0][0].to(node);
                printf("{\"node\": %d}\n", node);
            }
        }


    }
}

