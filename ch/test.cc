#include "query.h"
#include "contraction.h"
#include "dijkstra.h"

#include <pqxx/pqxx>
#include <map>
#include <iostream>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/archive/binary_oarchive.hpp>

#include <boost/graph/dijkstra_shortest_paths.hpp>

float secu(int cat, int length)
{
    switch(cat)
    {
        case 1: return length; break;
        case 2: return 1.3 * length; break;
        case 3: return 1.5 * length; break;
        case 4: return 2.0 * length; break;
        default: throw "Unknown category";
    }
}

int main(int, char** argv)
{
    Graph<2>::Type g;
    std::map<int, int> map;
    pqxx::connection Conn("dbname=mumoro");

    pqxx::work T(Conn, "Obtention du graphe");
    pqxx::result R = T.exec("SELECT source, destination, longueur, categorie1 FROM edge_paris_export");
   /* 
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
            map[source] = boost::add_vertex(g);
        if(map.find(destination) == map.end())
            map[destination] = boost::add_vertex(g);

        Graph<2>::Edge edge_prop;
        edge_prop.cost[0] = longueur;
        edge_prop.cost[1] = secu(categorie, longueur);
        boost::add_edge(map[source], map[destination], edge_prop, g);
        ++show_progress;
    }
    Graph<2>::Type g2(g);
    contract<2>(g);
    std::ofstream ofile2("graph_std_bin2");
    boost::archive::binary_oarchive oArchive2(ofile2);
    oArchive2 << g;

    std::ofstream ofile3("graph_std_2");
    boost::archive::binary_oarchive oArchive3(ofile3);
    oArchive3 << g2;
*/

    Graph<2>::Type g0, gc;
  /*  std::cout << "Chargement du graphe initial..." << std::endl;
    std::ifstream ifile("graph_std_2");
    boost::archive::binary_iarchive iArchive(ifile);
    iArchive >> g0;    // sérialisation de d
    std::cout << "   " << boost::num_vertices(g0) << " nœuds" << std::endl;
    std::cout << "   " << boost::num_edges(g0) << " arcs" << std::endl;
*/
    std::cout << "Chargement du graphe CH..." << std::endl;
    std::ifstream ifile2("graph_std_bin2");
    boost::archive::binary_iarchive iArchive2(ifile2);
    iArchive2 >> gc;    // sérialisation de d
    std::cout << "   " << boost::num_vertices(gc) << " nœuds" << std::endl;
    std::cout << "   " << boost::num_edges(gc) << " arcs" << std::endl;


  /*  BOOST_FOREACH(Graph<2>::edge_t edge, boost::edges(g2))
    {
        g2[edge].cost0 = g2[edge].cost[0];
    }
    BOOST_FOREACH(Graph<2>::edge_t edge, boost::edges(g))
    {
        g[edge].cost0 = g[edge].cost[0];
    }
    */BOOST_FOREACH(Graph<2>::edge_t edge, boost::edges(gc))
    {
        gc[edge].cost0 = gc[edge].cost[0];
    }
/*    BOOST_FOREACH(Graph<2>::edge_t edge, boost::edges(g0))
    {
        g0[edge].cost0 = g0[edge].cost[0];
    }
*/

/*    std::cout << "Longueur : " << query_mono<2>(atoi(argv[1]), atoi(argv[2]), gc) << std::endl;
    std::cout << "Longueur : " << query_mono<2>(atoi(argv[1]), atoi(argv[2]), gc) << std::endl;
    std::vector<int> p(boost::num_vertices(g0));
    std::vector<float> d(boost::num_vertices(g0));
    dijkstra_shortest_paths(g0, atoi(argv[1]), predecessor_map(&p[0]).distance_map(&d[0]).weight_map(get(&Graph<2>::Edge::cost0, g0)));
    std::cout << "Longueur 2 : " << d[atoi(argv[2])] << std::endl;
*/
 /*   std::ofstream dot("graph.dot");
    dot << "digraph G{" << std::endl;

    BOOST_FOREACH(Graph<2>::node_t node, boost::vertices(g))
    {
        dot << "N" << node << " [label=\"" << g[node].order << ";" << node << "\"];\n";
    }
    BOOST_FOREACH(Graph<2>::edge_t e, boost::edges(g))
    {
        if(g[e].shortcuted.size() == 0)
        {
            dot << "N" << boost::source(e,g) << " -> N" << boost::target(e,g) << ";\n";
        }
        else
        {
            dot << "N" << boost::source(e,g) << " -> N" << boost::target(e,g) << "[color=red];\n";
        }
    }
    dot << "}" << std::endl;

*/
/*
    for(int i = 0; i < 100; i++)
    {
        int start = rand() % boost::num_vertices(g0);
        int dest = rand() % boost::num_vertices(g0);
        std::vector<int> p(boost::num_vertices(gc));
        std::vector<float> d(boost::num_vertices(gc));
        dijkstra_shortest_paths(g0, start, predecessor_map(&p[0]).distance_map(&d[0]).weight_map(get(&Graph<2>::Edge::cost0, gc)));

        float cost = query_mono<2>(start, dest, gc); 
        if(cost > d[dest] + 0.1)
            std::cout << "fuck from " << start << " to " << dest << " cost: " << cost << " vs " << d[dest] << std::endl;
    }
*/
    int runs = 1000;
    std::vector<int> starts(runs);
    std::vector<int> dests(runs);
    for(int i=0; i < runs; i++)
    {
        starts.push_back(rand() % boost::num_vertices(gc));
        dests.push_back(rand() % boost::num_vertices(gc));
    }

/*
    { 
        boost::progress_timer t;
        for(int i=0; i < runs; i++)
        {
            std::vector<int> p(boost::num_vertices(gc));
            std::vector<float> d(boost::num_vertices(gc));
            dijkstra_shortest_paths(g0, starts[i], predecessor_map(&p[0]).distance_map(&d[0]).weight_map(get(&Graph<2>::Edge::cost0, gc)));
        }
    }*/
    {
        boost::progress_timer t;
        for(int i=0; i < runs; i++)
        {
            query_mono<2>(starts[i], dests[i], gc);
        }
    }
}
