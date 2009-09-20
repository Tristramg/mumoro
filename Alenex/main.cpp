#include "martins.h"
#include "MultimodalGraph.h"

#include "boost/date_time/posix_time/posix_time_types.hpp"
#include <stdlib.h>
#include <time.h>
#include <iomanip>
using namespace std;
using namespace boost::posix_time;

int main(int, char **)
{

    string nodes[3] = {"nodes_s.csv", "nodes_m.csv", "nodes_l.csv"};
    string edges[3] = {"edges_s.csv", "edges_m.csv", "edges_l.csv"};

    cout << "Starting first experiment: one-to-all"  << endl;
    cout << "StNodes StEdges toNodes toEdges   1 obj   2 obj   3 obj 3objrel nbLabel reLabel" << endl;
    for(int file=0; file < 3; file++)
    {
        MultimodalGraph g;
        std::string path = "data/";
        std::pair<int, int> a, b, c, d;

        d = g.load("bike", path + nodes[file], path + edges[file], Bike);
        a = g.load("foot", path + nodes[file], path + edges[file], Foot);
        b = g.load("bart", path + "stops_bart.txt", path+"stop_times_bart.txt", PublicTransport);
        c = g.load("muni", path + "stops_muni.txt", path+"stop_times_muni.txt", PublicTransport);

        Edge interconnexion;
        interconnexion.distance = 0;
        interconnexion.duration = Duration(30);
        interconnexion.elevation = 0;
        interconnexion.cost = 0;
        interconnexion.nb_changes = 1;

        g.connect_closest("foot", "bart", interconnexion);
        g.connect_closest("foot", "muni", interconnexion);
        g.connect_same_nodes("bike", "foot", interconnexion, false);

        srand ( time(NULL) );

        float nb_runs = 10;

        cout << a.first << setw(8)
            << a.second << setw(8)
            <<  boost::num_vertices(g.graph()) << setw(8)
            << boost::num_edges(g.graph()) << setw(8) << flush;

        size_t labels = 0, labels_relaxed = 0;
        vector<node_t> starts;
        for(int obj = 1; obj <= 3; obj++)
        {
            ptime stime(microsec_clock::local_time());
            for(int i=0; i<nb_runs; i++)
            {
                node_t start = rand() % d.first;
                if(obj == 1)
                    martins(start, invalid_node, g);
                if(obj == 2)
                    martins(start, invalid_node, g, &Edge::nb_changes);
                if(obj == 3)
                {
                    labels = martins(start, invalid_node, g, &Edge::nb_changes, &Edge::elevation)[0].permanent_labels_count;
                    starts.push_back(start);
                }
            }
            ptime etime(microsec_clock::local_time());

            cout << ((etime - stime).total_milliseconds()) / nb_runs << setw(8) << flush;
       }
        ptime stime(microsec_clock::local_time());
        for(int i=0; i<nb_runs; i++)
        {
            labels_relaxed = relaxed_martins(starts[i], invalid_node, g, &Edge::nb_changes, &Edge::elevation)[0].permanent_labels_count;
        }
        ptime etime(microsec_clock::local_time());
        cout << (etime - stime).total_milliseconds() / nb_runs << setw(8) 
            << labels << setw(8)
            << labels_relaxed << endl;

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

        }

    }

}
