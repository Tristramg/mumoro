#include "graph.h"
#include "query.h"
// Functor comparant la priorité d'un nœud
// TODO : y'a vraiment besoin de passer le graph en réf ?
struct priority_comp
{
    const Graph::Type & g; 
    priority_comp(const Graph::Type & graph) : g(graph) {}

    bool operator()(Graph::node_t a, Graph::node_t b) const
    {
        return (g[a].priority < g[b].priority);
    }
};

// Calcule la priorité d'un nœud. Il s'agit d'une valeur purement heuristique pour
// classer les nœuds
// On utilise l'heuristique Edge-Diffirence qui calcule combien d'arcs seront rajoutés
// par rapport au nombre d'arcs supprimés
// On simule donc la suppression
//
// Un tout petit changement de cette heuristique, et le temps de contraction et d'execution varient d'un facteur 10 (et pas toujours dans le même sens..
int Graph::node_priority(Graph::node_t node)
{
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
                  /*  Edge edge_prop(graph[in_edge]);
                    for(int i=0; i < Graph::objectives ; i++)
                    {
                        edge_prop.cost[i] += graph[out_edge].cost[i];
                    }
*/
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
//
// Retourne le nombre d'arcs rajoutés
int Graph::suppress(node_t node)
{
    int shortcuts = 0;
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
                    //Il n'existe pas de plus court chemin entre pred et succ
                    // Bon... bizarrement, ça ne change rien... un simple test d'existance
                    // d'un arc domminé pourrait ptet suffir... Ça contredit un peu le mémoire
                    // de Geisberger
                    Edge edge_prop(graph[in_edge]);
                    for(int i=0; i < N; i++)
                        {
                            edge_prop.cost[i] += graph[out_edge].cost[i];
                        }
            //        if (!martins_witness(pred, succ, edge_prop.cost, graph))
                    {
                        // Note sur les itérateurs :
                        // Ce n'est faisable que parce que les arcs sont stoqués sous forme de listS
                        // Sinon ça merde sur les itérateurs dans la boucle
                        Edge edge_prop(graph[in_edge]);
                        for(int i=0; i < N; i++)
                        {
                            edge_prop.cost[i] += graph[out_edge].cost[i];
                        }
                        bool exists;
                        edge_t existing_edge;
                        boost::tie(existing_edge, exists) = boost::edge(pred, succ, graph);
                        if(exists)
                        {
                            cost_t ecost = graph[existing_edge].cost;
                            //Si le coût est dominé par l'existant, on ne fait rien
                            if(dominates(ecost,  edge_prop.cost) || ecost == edge_prop.cost)
                            //if(graph[existing_edge].cost[0] < edge_prop.cost[0])
                            {
                            }
                            //Si le nouveau cout domine, on modifie la valeur
                            else if(dominates(edge_prop.cost, ecost))
                            //else if(true)
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
                            //Propriétés du nouvel arc
                            edge_prop.shortcuted.push_back(node);
                            boost::add_edge(pred, succ, edge_prop, graph);
                            shortcuts++;
                        }
                    }
                }
            }
        }
    }
    return shortcuts;
}



//Fonction globale qui effectue la contraction
//Phase 1 : trier les nœuds par leur priorité
//Phase 2 : prendre récursivement le plus petit nœud non encore traité et l'éliminer
//Phase 3 : on supprime tous 
void Graph::contract()
{
    int shortcuts = 0;

    boost::mutable_queue<node_t, std::vector<node_t>, priority_comp> queue(boost::num_vertices(graph), priority_comp(graph), boost::identity_property_map());
    std::cout << "Nombre d'arcs avant la contraction : " << boost::num_edges(graph) << std::endl;
    //Phase 1
    int positive = 0;
    int negative = 0;
    int zero = 0;
    std::cout << "Simulation de la contraction pour déterminer l'ordre de contraction" << std::endl;
    boost::progress_display show_progress( boost::num_vertices(graph) );
    BOOST_FOREACH(node_t node, boost::vertices(graph))
    {
        int i = node_priority(node);
        graph[node].priority = i;
        graph[node].order = Node::undefined;
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
        if(node_priority(node) != graph[node].priority)
        {
            //Bon gros hack car je ne vois pas comment itérer sur les élements de la queue
            //TODO: itérer que sur la queue
            BOOST_FOREACH(node_t n, boost::vertices(graph))
            {
                if(graph[n].order == Graph::Node::undefined)
                {
                    graph[n].priority = node_priority(n);
                    queue.update(n);
                }
            }
        }

        node = queue.top();
        queue.pop();
        BOOST_ASSERT(graph[node].order == Node::undefined);

        // On arrête de rajouter des arcs à partir d'un certain moment
        if(graph[node].priority <= 10000)
        {
            graph[node].order = current_order++;
            shortcuts += suppress(node);
            //On met à jour la priorité des nœuds sortant (les entrants sont soit déjà traités,
            //soit l'arc a été supprimé car c'est forcément un nœud plus grand)
            BOOST_FOREACH(edge_t out_edge, boost::out_edges(node, graph))
            {
                node_t succ = boost::target(out_edge, graph);
                if(graph[succ].order == Node::undefined)
                {
                    graph[succ].priority = node_priority(succ); 
                    queue.update(succ);
                }
            }

        }
        else
        {
            graph[node].order = current_order;
            while( !queue.empty() )
            {
                graph[queue.top()].order = current_order;
                queue.pop();
            }
        }
        BOOST_ASSERT(graph[node].order != Node::undefined);

        ++show_progress2;
    }

    std::cout << "Nombre de racourcis ajoutés : " << shortcuts << std::endl;
    std::cout << "Nombre d'arcs après la contraction : " << boost::num_edges(graph) << std::endl;

    split();
}


