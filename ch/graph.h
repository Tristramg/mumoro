// Définit les structures de données pour un graphe
// permettant un calcul d'itinéraire multiobjectif
//

#include <boost/graph/compressed_sparse_row_graph.hpp>

#include <boost/pending/mutable_queue.hpp>
#include <boost/graph/adjacency_list.hpp>
#include <boost/array.hpp>
#include <boost/graph/adj_list_serialize.hpp>
#include <boost/serialization/list.hpp>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/archive/binary_oarchive.hpp>
#include <boost/foreach.hpp>
#include <boost/progress.hpp>

#include <iostream>
#include <fstream>

#ifndef GRAPH_H
#define GRAPH_H


using namespace boost;
using namespace boost::multi_index;

// La structure est templatée en fonction du nombre d'objectifs
struct Graph
{
    static const int objectives = 2;
    static const int N = 2;
    typedef array<float, objectives> cost_t;

    bool static dominates(cost_t a, cost_t b)
    {
        for(int i=0; i < N; i++)
        {
            if(a[i] > b[i])
                return false;
        }
        //Si on veut qu'il y ait au moins un i tel que a[i] < b[i] 
        return a != b;
    }

    struct Node
    {
        static const int undefined = -1;
        int order; // Définit l'ordre du nœud dans le graphe
        int id; // Identifiant orginal
        int priority; // Valeur de l'heuristique TODO: penser à le foutre à l'extérieur de la map...

        Node() : order(undefined) {} // Par défaut, l'ordre du nœud est indéfini

        //Permet de sérialiser dans un fichier le graphe
        template<class Archive>
            void serialize(Archive& ar, const unsigned int version)
            {
                ar & order & id & priority;
            }
    };

    struct Edge
    {
        float cost0;
        cost_t cost; // Coût multiobjectif de l'arc
        std::list<int> shortcuted; // Nœuds court-circuités par cet arc. La liste est vide si c'est un arc original

        //Permet de sérialiser dans un fichier le graphe
        template<class Archive>
            void serialize(Archive& ar, const unsigned int version)
            {
                ar & cost & shortcuted;
            }
    };

    //NOTE: comme on modifie à tours de bras les arcs, il est important que les arcs soient
    //stockés dans une liste (problème de perfs et d'invalidation d'itérateurs)
    // (c'est le premier paramètre du template)
    typedef boost::adjacency_list<boost::listS, boost::vecS, boost::bidirectionalS, Node, Edge > Type;
    typedef boost::graph_traits<Type>::edge_descriptor edge_t;
    typedef boost::graph_traits<Type>::vertex_descriptor node_t;

    typedef compressed_sparse_row_graph<boost::directedS, Node, Edge>  CType;

    Type graph;

    Graph()
    {}

    Graph(std::string filename)
    {
        std::cout << "Loading graph from file " << filename << std::endl;
        std::ifstream ifile(filename.c_str());
        boost::archive::binary_iarchive iArchive(ifile);
        iArchive >> graph;   
        std::cout << "   " << boost::num_vertices(graph) << " nodes" << std::endl;
        std::cout << "   " << boost::num_edges(graph) << " edges" << std::endl;
    }

    node_t add_node()
    {
        return boost::add_vertex(graph);
    }

    node_t add_node(Node n)
    {
        return boost::add_vertex(n, graph);
    }

    std::pair<edge_t, bool> add_edge(node_t source, node_t target, Edge edge)
    {
        return boost::add_edge(source, target, edge, graph);
    }

    Node & operator[](node_t n)
    {
        return graph[n];
    }

    const Node & operator[](node_t n) const
    {
        return graph[n];
    }


    const Edge & operator[](edge_t e) const
    {
        return graph[e];
    }


    void save(std::string filename)
    {
        std::ofstream ofile(filename.c_str());
        boost::archive::binary_oarchive oArchive(ofile);
        oArchive << graph;
    }

    int num_vertices() const
    {
        return boost::num_vertices(graph);
    }

    
    int node_priority(Graph::node_t node);
    int suppress(node_t node);
    void contract();
};

#endif
