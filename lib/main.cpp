#include "martins.h"
#include "MultimodalGraph.h"

#include "boost/date_time/posix_time/posix_time_types.hpp"
#include <stdlib.h>
#include <time.h>
#include "tsaggouris.h"

using namespace std;
using namespace boost::posix_time;

int main(int argc, char *argv[])
{
//    char * nodes[3] = {"nodes_s.csv", "nodes_m.csv", "nodes_l.csv"};
//    char * edges[3] = {"edges_s.csv", "edges_m.csv", "edges_l.csv"};

    cout << "Starting first experiment: one-to-all"  << endl;
    cout << "StreetNodes StreetEdges TotalNodes TotalEdges 1obj 2obj 3obj 4obj" << endl;
    for(int file=0; file < 1; file++)
    {
        MultimodalGraph g;
        g.init_pg("dbname=mumoro");
        std::string path = "./";
//        std::string path = "/home/tristram/MOSPP-instances/instances/San Francisco/";
        std::pair<int, int> a, b, c, d;

        //d = g.load_pg("bike", "tlse_nodes", "tlse_edges", Bike);
        a = g.load_pg("foot", "tlse_nodes", "tlse_edges", Foot);
        d = g.load("bike", path + "nodes.csv", path + "edges.csv", Bike);
        // b = g.load("bart", path + "stops_bart.txt", path+"stop_times_bart.txt", PublicTransport);
        // c = g.load("muni", path + "stops_muni.txt", path+"stop_times_muni.txt", PublicTransport);

        Edge interconnexion;
        interconnexion.distance = 0;
        interconnexion.duration = Duration(30);
        interconnexion.elevation = 0;
        interconnexion.cost = 0;
        interconnexion.nb_changes = 1;

//        g.connect_closest("foot", "bart", interconnexion);
        //g.connect_closest("foot", "muni", interconnexion);
        g.connect_same_nodes("bike", "foot", interconnexion, false);

        srand ( time(NULL) );

        cout << a.first << " " << a.second << " " <<  boost::num_vertices(g.graph()) << " " << boost::num_edges(g.graph()) << flush;
        ptime stime(microsec_clock::local_time());
        node_t start = rand() % d.first + a.first; 
        node_t dest = rand() % a.first;

        //   relaxed_martins(start, invalid_node, g, &Edge::nb_changes, &Edge::elevation);
        ptime etime(microsec_clock::local_time());
        cout << " " << (etime - stime).total_milliseconds() << endl;

        vector<Path> p = martins(start, dest, g, &Edge::nb_changes, 30000);
        cout << "==" << p.size() << "==" << endl;
        //ssmosp(g, start);
        ptime ftime(microsec_clock::local_time());
        cout << " " << (ftime - etime).total_milliseconds() << endl;
        /*
           for(int obj = 1; obj <= 3; obj++)
           {
           if(file == 2 && obj == 4)
           {
           cout << " ---" << flush;
           }
           else
           {
           ptime stime(microsec_clock::local_time());
           for(int i=0; i<10; i++)
           {
           node_t start = rand() % d.first;
           if(obj == 1)
           martins(start, invalid_node, g);
           if(obj == 2)
           martins(start, invalid_node, g, &Edge::nb_changes);
           if(obj == 3)
           martins(start, invalid_node, g, &Edge::nb_changes, &Edge::elevation);
           }

           ptime etime(microsec_clock::local_time());
           cout << " " << ((etime - stime).total_milliseconds()) / nb_runs << flush;
           }
           }
           cout << endl;

           if( file == 2 )
           {
           cout << endl << "Starting second experiment: one-to-one" << endl;
           cout << "Distance 2obj 3 obj" << endl;
           for(int i=0; i< 100; i++)
           {
           node_t start = rand() % d.first;
           node_t end = rand() % a.first + d.first;
           ptime stime(microsec_clock::local_time());
           martins(start, end, g, &Edge::nb_changes);
           ptime etime(microsec_clock::local_time());
           martins(start, end, g, &Edge::nb_changes, &Edge::elevation);
           ptime etime2(microsec_clock::local_time());

           cout << distance(g[start].lon, g[start].lat, g[end].lon, g[end].lat) << " " << (etime - stime).total_milliseconds() << " " << (etime2 - etime).total_milliseconds() << endl;
           }

           cout << endl << "Starting third experiment: relaxed dominance" << endl;
           cout << "Usual dominance  Relaxed dominance" << endl;
           ptime stime(microsec_clock::local_time());
           for(int i=0; i<10; i++)
           {
           node_t start = rand() % d.first;
           relaxed_martins(start, invalid_node, g, &Edge::nb_changes, &Edge::elevation);
           }

           ptime etime(microsec_clock::local_time());
           cout << (etime - stime).total_milliseconds();
           }
           */
    }

}
