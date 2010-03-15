// Effectue l'étape de contraction du graphe
// TODO : réfléchir comment foutre le tout dans une classe au lieu de passer toujours graph en paramètre
// (accessoirement, ça ferait moins de typenames et de <N> qui trainent)
#include <boost/progress.hpp>

#include "graph.h"
#include "martins.h"

#include <boost/pending/mutable_queue.hpp>
#include <boost/property_map/property_map.hpp>
#include <iostream>

#ifndef CONTRACTION_H
#define CONTRACTION_H

int shortcuts;

// Calcule la priorité d'un nœud. Il s'agit d'une valeur purement heuristique pour
// classer les nœuds
// On utilise l'heuristique Edge-Diffirence qui calcule combien d'arcs seront rajoutés
// par rapport au nombre d'arcs supprimés
// On simule donc la suppression
template<class Graph>
int node_priority(typename Graph::node_t node, const typename Graph::Type & graph)
{
    typedef typename Graph::node_t node_t;
    typedef typename Graph::edge_t edge_t;
    int added = 0;
    //Pour tous les prédecsseurs de node
    BOOST_FOREACH(edge_t in_edge, boost::in_edges(node, graph))
    {
        node_t pred = boost::source(in_edge, graph);
        if(graph[pred].order == Graph::Node::undefined)
        {
            //Pour tous les successeurs de node
            BOOST_FOREACH(edge_t out_edge, boost::out_edges(node, graph))
            {
                node_t succ = boost::target(out_edge, graph);
                if(graph[succ].order == Graph::Node::undefined)
                {
                    typename Graph::Edge edge_prop(graph[in_edge]);
                    for(int i=0; i < Graph::objectives ; i++)
                    {
                        edge_prop.cost[i] += graph[out_edge].cost[i];
                    }

                    //Il n'existe pas de plus court chemin entre pred et succ
//                    if (!witness_martins<N>(pred, succ, graph, edge_prop.cost))
                    {
                        added++;
                    }
                }
            }
        }
    }
    return added - (boost::out_degree(node, graph) + boost::in_degree(node, graph));
}


// Fonction qui effectivement élimine le nœud en le court-circuitant par des arcs
// On étant un prédecesseur s et un successeur t, avec s > t
// on crée l'arc s->t donc le cout est  c(s->u) + c(u->t)
// s'il n'existe aucun "witness" (autre chemin de moindre coût)
    template<class Graph>
void suppress(typename Graph::node_t node, typename Graph::Type & graph)
{
    typedef typename Graph::node_t node_t;
    typedef typename Graph::edge_t edge_t;
    //Pour tous les prédecsseurs de node
    BOOST_FOREACH(edge_t in_edge, boost::in_edges(node, graph))
    {
        node_t pred = boost::source(in_edge, graph);
        if(graph[pred].order == Graph::Node::undefined)
        {
            //Pour tous les successeurs de node
            BOOST_FOREACH(edge_t out_edge, boost::out_edges(node, graph))
            {
                node_t succ = boost::target(out_edge, graph);
                if(graph[succ].order == Graph::Node::undefined && pred != succ)
                {
                    //Propriétés du nouvel arc
                    typename Graph::Edge edge_prop(graph[in_edge]);
                    for(int i=0; i < Graph::objectives; i++)
                    {
                        edge_prop.cost[i] += graph[out_edge].cost[i];
                    }

                    //Il n'existe pas de plus court chemin entre pred et succ
                   // if (!witness_martins<N>(pred, succ, graph, edge_prop.cost))
                    {
                        // On note le nœud court-circuité pour dérouler le chemin à la fin de la requète

                        // Note sur les itérateurs :
                        // Ce n'est faisable que parce que les arcs sont stoqués sous forme de listS
                        // Sinon ça merde sur les itérateurs dans la boucle
                        bool exists;
                        edge_t existing_edge;
                        boost::tie(existing_edge, exists) = boost::edge(pred, succ, graph);
                        if(exists)
                        {
                            //Si le coût est dominé par l'existant, on ne fait rien
                            //if(dominates<N>(graph[existing_edge].cost,  edge_prop.cost))
                            if(graph[existing_edge].cost[0] < edge_prop.cost[0])
                            {
//                                std::cout << "Case 1" << std::endl;
                            }
                            //Si le nouveau cout domine, on modifie la valeur
//                            else if(dominates<N>(edge_prop.cost, graph[existing_edge].cost))
                            else if(true)
                            {
                                graph[existing_edge].cost = edge_prop.cost;
                            }
                            //Sinon on le rajoute en parallèle
                            else
                            {
                                edge_prop.shortcuted.push_back(node);
                                boost::add_edge(pred, succ, edge_prop, graph);
                                shortcuts++;
                            }
                        }
                        else
                        {
                            edge_prop.shortcuted.push_back(node);
                            boost::add_edge(pred, succ, edge_prop, graph);
                            shortcuts++;
                        }
                    }
                }
            }
        }
    }
}


// Functor comparant la priorité d'un nœud
template<class Graph>
struct priority_comp
{
    const typename Graph::Type & graph;
    priority_comp(const typename Graph::Type & g) : graph(g) {}

    bool operator()(const typename Graph::node_t a, const typename Graph::node_t b) const
    {
        return (graph[a].priority < graph[b].priority);
    }
};

//Fonction globale qui effectue la contraction
//Phase 1 : trier les nœuds par leur priorité
//Phase 2 : prendre récursivement le plus petit nœud non encore traité et l'éliminer
//Phase 3 : on supprime tous 
    template<class Graph>
void contract(typename Graph::Type & graph)
{
    shortcuts = 0;
    typedef typename Graph::node_t node_t;
    typedef typename Graph::edge_t edge_t;

    priority_comp<Graph> comp(graph);
    boost::mutable_queue<node_t, std::vector<node_t>, priority_comp<Graph> > queue(boost::num_vertices(graph), comp, boost::identity_property_map());
    std::cout << "Nombre d'arcs avant la contraction : " << boost::num_edges(graph) << std::endl;
    //Phase 1
    int positive = 0;
    int negative = 0;
    int zero = 0;
    std::cout << "Simulation de la contraction pour déterminer l'ordre de contraction" << std::endl;
    boost::progress_display show_progress( boost::num_vertices(graph) );
    BOOST_FOREACH(node_t node, boost::vertices(graph))
    {
        int i = node_priority<Graph>(node, graph);
        graph[node].priority = i;
        graph[node].order = Graph::Node::undefined;
        if(i < 0)
            negative++;
        else if(i == 0)
            zero++;
        else
            positive++;

        queue.push(node);
        ++show_progress;
    }
    std::cout << "Nombre de nœuds à edge diff positive : " << positive << std::endl;
    std::cout << "Nombre de nœuds à edge diff nulle : " << zero << std::endl;
    std::cout << "Nombre de nœuds à edge diff négative : " << negative << std::endl << std::endl;

    int current_order = 0;
    std::cout << "Effectue la contraction à proprement parler" << std::endl;
    boost::progress_display show_progress2( boost::num_vertices(graph) );
    while( !queue.empty() )
    {
        node_t node = queue.top();
        if(node_priority<Graph>(node, graph) != graph[node].priority)
        {
            //Bon gros hack car je ne vois pas comment itérer sur les élements de la queue
            //TODO: itérer que sur la queue
            BOOST_FOREACH(node_t n, boost::vertices(graph))
            {
                if(graph[n].order == Graph::Node::undefined)
                {
                    graph[n].priority = node_priority<Graph>(n, graph);
                    queue.update(n);
                }
            }
        }
//        std::cout << "Queue : " << queue.size() << ", priority : " << graph[node].priority  << std::endl;
        node = queue.top();
        queue.pop();

        if(graph[node].order != Graph::Node::undefined)
            std::cout << "WTF ?!" << std::endl;
        graph[node].order = current_order++;
        suppress<Graph>(node, graph);
        
        //On met à jour la priorité des nœuds sortant (les entrants sont soit déjà traités,
        //soit l'arc a été supprimé car c'est forcément un nœud plus grand)
        BOOST_FOREACH(edge_t out_edge, boost::out_edges(node, graph))
        {
            node_t succ = boost::target(out_edge, graph);
            if(graph[succ].order == Graph::Node::undefined)
            {
                graph[succ].priority = node_priority<Graph>(succ, graph); 
                queue.update(succ);
            }
        }

        ++show_progress2;
    }

    std::cout << "Nombre de racourcis ajoutés : " << shortcuts << std::endl;
    std::cout << "Nombre d'arcs après la contraction : " << boost::num_edges(graph) << std::endl;
}

#endif
