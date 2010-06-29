#include "graph.h"
#include "query.h"

#include <pqxx/pqxx>
#include <map>
#include <iostream>


void bench(Graph & g, Graph & gc);
void martins_bench(Graph & g, Graph & gc);
void test(Graph & g, Graph & gc);
float secu(int cat, int length)
{
    switch(cat)
    {
        case 0: return length; break;
        case 1: return length; break;
        case 2: return 1.3 * length; break;
        case 3: return 1.5 * length; break;
        case 4: return 2.0 * length; break;
        case 5: return 2.0 * length; break;
        default: throw "Unknown category";
    }
}

int main(int, char** argv)
{
    Graph g;
    std::map<int, int> map;
    pqxx::connection Conn("dbname=mumoro");

    pqxx::work T(Conn, "Obtention du graphe");
    pqxx::result R = T.exec("SELECT source, destination, longueur, categorie1 FROM edge_paris_export");
    //pqxx::result R = T.exec("SELECT source, target, length, bike FROM sf_edges");
    
    boost::progress_display show_progress( R.size() );

    for (pqxx::result::const_iterator i = R.begin(); i != R.end(); ++i)
    {
        int source, destination, categorie;
        float longueur;
        (*i)[0].to(source);
        (*i)[1].to(destination);
        (*i)[2].to(longueur);
        (*i)[3].to(categorie);

        if(map.find(source) == map.end())
            map[source] = g.add_node();
        if(map.find(destination) == map.end())
            map[destination] = g.add_node();

        Graph::Edge edge_prop;
        edge_prop.cost[0] = longueur;
        edge_prop.cost[1] = secu(categorie, longueur);
        g.add_edge(map[source], map[destination], edge_prop);
//        g.add_edge(map[destination], map[source], edge_prop);
        ++show_progress;
    }
    g.save("paris_original");
    Graph gc(g);
    gc.contract();
    gc.save("paris_ch");
   
    //   51937 nodes
//   619894 edges


    
/*    Graph g("sf_original");
    Graph gc(g);//("sf");
    gc.contract();
    gc.save("sf2");*/
    //    51937 nodes
//   619894 edges
    
  // Graph g("paris_original");
  //Graph gc("paris_ch");
/*  gc.split();
  gc.save("paris_ch");*/
//    Graph gc(g);
//    gc.contract();
//    gc.save("paris_ch");
   // martins(10000, 12, g);
   // ch_martins(10000, 12, gc);

    //test(g,gc); 
//    bench(g, gc);
    martins_bench(g, gc);


}
