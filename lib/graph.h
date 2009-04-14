/*
 * File:   graph.h
 * Author: tristram
 *
 * Created on July 24, 2008, 9:50 AM
 */

#include <limits.h>
#include <boost/graph/graph_traits.hpp>
#include <boost/graph/dijkstra_shortest_paths.hpp>
#include <boost/graph/compressed_sparse_row_graph.hpp>
#include <boost/shared_ptr.hpp>
#include "boost/date_time/posix_time/posix_time.hpp"


#ifndef _GRAPH_H
#define _GRAPH_H

namespace Mumoro
{

    struct Cost_function {
        virtual double operator()( double ) const = 0;
    };

    typedef boost::shared_ptr<Cost_function> FunctionPtr;

    class Const_cost : public Cost_function
    {
        double m_cost;
        public:
        Const_cost(double);
        virtual double operator()(double) const;
    };

    class Velouse_cost : public Cost_function
    {
        boost::posix_time::time_duration m_opening, m_open_duration;
        double m_cost;
        public:
        Velouse_cost(boost::posix_time::time_duration, boost::posix_time::time_duration, double);
        virtual double operator()(double) const;
    };

    typedef enum {Foot, Bike, Car, Subway, Bike_at_hand, Switch, Bus, NaM} Transport_mode;
    /** Properties of an edge */
    struct Edge_property
    {
        int link_id; /**< identifiant du chaînon dans la base */
        FunctionPtr cost; /**< cost function on the edge */
        double length; /**< length of the link in meters */
        unsigned int first; /**< Identifiant du nœud de départ renuméroté */
        unsigned int second; /**< Identifiant du nœud d'arrivée renuméroté */
        Transport_mode mode; /**< What mean of transport does this link belongs to */
        /** Compare lexicalement par rapport à first puis second */
        bool operator<(Edge_property e) const;
    };

    /** Describes a node */
    class Node
    {
        public:
            uint64_t id; /**< id of the node */
            double lon; /**< longitude in decimal degrees */
            double lat; /**< latitude in decimal degrees */
    };

     /** Défini les caractéristiques du graphe :
     * — forme compacte pour optimiser les performances (contre-partie : contruction plus délicate)
     * — graphe orienté
     * — caractéristiques des nœuds sont Vertex_property
     * — caractéritisques des arcs sont Edge_property
     *
     * Le graphe doit être construit en fournissant une liste ordonnée lexicalement de couples de nœuds <dépat,arrivée>
     * Les idenfiants des nœuds doivent nécessairement commencer à 0 et former une séquence
     */
    typedef boost::compressed_sparse_row_graph<boost::directedS, Node, Edge_property > CGraph;

    /** Définit un nœud du graphe */
    typedef boost::graph_traits<CGraph>::vertex_descriptor cvertex;

    /** Définit un arc du graphe */
    typedef boost::graph_traits<CGraph>::edge_descriptor cedge;
}

#endif

