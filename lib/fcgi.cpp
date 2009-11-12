#include "martins.h"
#include <boost/algorithm/string.hpp>
#include <boost/algorithm/string/split.hpp>
#include <boost/regex.hpp>
#include <boost/lexical_cast.hpp>
#include "fcgi_stdio.h"
#include <iomanip>

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
  bool fail = false;
  MultimodalGraph g;
  g.init_pg("dbname=mumoro user=tristram");
  //std::string path = "../instances/San Francisco/";
  std::pair<int, int> a, b, c, d;
  std::string path = "/Library/WebServer/Documents/gtfs/";
 
  a = g.load_pg("foot", "sf_nodes", "sf_edges", Foot);
  d = g.load_pg("bike", "sf_nodes", "sf_edges", Bike);
  b = g.load("bart", path + "stops_bart.txt", path+"stop_times_bart.txt", PublicTransport);

  Edge interconnexion;
  interconnexion.distance = 0;
  interconnexion.duration = Duration(30);
  interconnexion.elevation = 0;
  interconnexion.cost = 0;
  interconnexion.nb_changes = 1;
  cout << "Bart: " << b.first << " " << b.second << endl;

  cout << "Foot: " << a.first << " " << a.second << endl;

  g.connect_same_nodes("bike", "foot", interconnexion, false);
  g.connect_closest("foot", "bart", interconnexion);

  while(FCGI_Accept() >= 0)
  {
     printf("Content-type: application/json\r\n\r\n");
     char * query_string = getenv("QUERY_STRING");
     string escaped = un_escape(query_string);
     map<string,string> query_map = parse(escaped);
     std::stringstream output;
     output << setprecision(9);
     std::stringstream error_msg;

     map<string,string>::iterator it = query_map.begin();

     if(query_map.find("start") == query_map.end())
     {
       error_msg << "No start defined. ";
       fail = true;
     }

     if(query_map.find("dest") == query_map.end())
     {
       error_msg << "No destination defined. ";
       fail = true;
     }

     if(!g.layers["bike"].exists(query_map["start"]))
     {
	     error_msg << "Start node(" << query_map["start"] << ") not found. ";
	     fail = true;
     }

     if(!g.layers["bike"].exists(query_map["dest"]))
     {
	     error_msg << "Destination node(" << query_map["dest"] << ") not found. ";
	     fail = true;
     }

     if(fail)
     {
       output << "{\"error\": \"" << error_msg.str() << "\"}";
       printf("%s", output.str().c_str());
     }

     else
     {
       std::vector<Path> p;
       p = martins(boost::lexical_cast<int>(g.layers["bike"][query_map["start"]]),
           boost::lexical_cast<int>(g.layers["foot"][query_map["dest"]]), g, &Edge::nb_changes);
       bool first_path = true;
       output << "{\n \"paths\":\n    [";
       for(std::vector<Path>::const_iterator i = p.begin(); i != p.end(); i++)
       {
         if(first_path) first_path = false;
         else output << ",\n";
         stringstream path; path << setprecision(9);
         path << "\n    {\"cost\": [" << i->cost[0];
         for(size_t ci = 1; ci < i->cost.size(); ci++)
           path << ", " << i->cost[ci];
         path << "]," << endl;
         path << "     \"string\":\n        [" << endl;
         bool first = true;
         for(list<Node>::const_iterator ni = i->nodes.begin(); ni != i->nodes.end(); ni++)
         {
           if(first)
             first = false;
           else
             path << "," << endl;
           path << "        [" << ni->lon << "," << ni->lat << "]";
         }
         path << "\n        ]\n    }";
         output << path.str();
       }
       output << "\n    ]\n}\n";
       printf("%s", output.str().c_str());
     }
  }

  return 0;
}
