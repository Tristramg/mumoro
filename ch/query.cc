#include "query.h"
#include <functional>
using namespace boost::multi_index;
int Graph::comps = 0;

// Décrit une étiquette (label) utilisée pendant l'exploration
// Cela représente un état de l'exploration et un chemin possible
struct Label
{
    Graph::cost_t cost; // coût du chemin
    Graph::node_t node; // nœud destination du chemin
    boost::shared_ptr<Label> predecessor;
};

bool dominates(const Label & a, const Label & b)
{
    return Graph::dominates(a.cost, b.cost);
}

struct Label_dom
{
    Label l;
    Label_dom(const Label & _l) : l(_l) {}
    bool operator()(const Label & b)
    {
        return dominates(l, b) || l.cost == b.cost;
    }
};

typedef boost::shared_ptr<Label> LabelPtr;

struct my_queue
{

    typedef boost::multi_index_container<
        Label,
        indexed_by<
            ordered_non_unique<member<Label, Graph::cost_t, &Label::cost> >,
        hashed_non_unique<member<Label, Graph::node_t, &Label::node > >
            >
            > Type;

    typedef nth_index<Type, 0>::type& by_cost;
    typedef nth_index<Type, 1>::type& by_nodes;
    typedef nth_index<Type, 1>::type::iterator nodes_it;
};



// Étant donné une étiquette, il reconstruit le chemin
// Également insère les nœuds court-circuités
Path unpack(LabelPtr label_ptr, const Graph & graph)
{
    LabelPtr nullPtr;
    Path p;
    p.cost = label_ptr->cost;

    while(label_ptr != nullPtr)
    {
        p.nodes.push_front( label_ptr->node );

        // S'il y a un prédecesseur, on déroule les nœuds court-circuités
        if( label_ptr->predecessor != nullPtr )
        {
            bool b;
            Graph::edge_t edge; 
            boost::tie(edge, b) = boost::edge(label_ptr->predecessor->node, label_ptr->node, graph.graph);

            BOOST_ASSERT(b); // On s'assure que l'arc pred->label existe bien

            // Pour tout nœud qui avait été count-circuité
            BOOST_FOREACH(int n, graph[edge].shortcuted)
            {
                p.nodes.push_front(n);
            }
        }
        label_ptr = label_ptr->predecessor;
    }

    return p;
}

// Calcule les plus courts chemins entre deux nœuds
// Retourne une liste de chemins
std::list<Path> query(Graph::node_t source, Graph::node_t target, const Graph::Type & graph)
{
    //TODO : implémeter
    std::list<Path> paths;
    return paths;
}

    template<class Container>
bool is_dominated_by_any(const Container & c, const Label & l)
{
    BOOST_FOREACH(Label a,  c )
    {
        if( dominates(a, l) || a.cost == l.cost)
        {
            return true;
        }
    }
    return false;
}

// Algo de martins sur le graphe normal
bool martins(Graph::node_t start_node, Graph::node_t dest_node, const Graph & g)
{
    my_queue::Type Q;
    Graph::comps = 0;
    std::vector< std::deque<Label> > P(num_vertices(g.graph));

    Label start;
    start.node = start_node;
    for(int i=0; i < Graph::objectives; i++)
        start.cost[i] = 0;

    Q.insert(start);
    const  my_queue::by_cost cost_q_it = Q.get<0>();
    const  my_queue::by_nodes node_q = Q.get<1>();

    int visited = 0;
    while( !Q.empty() )
    {
        Label l = *(cost_q_it.begin());
        visited++;
        P[l.node].push_back(l);
        //        std::cout << "Label! node=" << l.node << " [" << l.cost[0] << "," << l.cost[1] << "]" << std::endl;
        Q.erase(cost_q_it.begin());
        BOOST_FOREACH(Graph::edge_t e, out_edges(l.node, g.graph))
        {
            Label l2;
            l2.node = boost::target(e, g.graph);
            for(int i=0; i < Graph::objectives; i++)
                l2.cost[i] = l.cost[i] + g[e].cost[i];

            if(!is_dominated_by_any(node_q.equal_range(l2.node), l2) && !is_dominated_by_any(P[l2.node],l2) && !is_dominated_by_any(P[dest_node], l2))
            {
                my_queue::nodes_it it, end;
                tie(it, end) = node_q.equal_range(l2.node);
                while(it != end)
                {
                    if(Graph::dominates(l2.cost, it->cost) || l2.cost == it->cost)
                        it = Q.get<1>().erase(it);
                    else
                    {
                        it++;
                    }
                }
                Q.insert(l2);
            }
        }
    }

    std::cout << "Labels visited: " << visited << ", solutions found: " << P[dest_node].size() << ", dominations tests: " << Graph::comps << std::endl;
 /*   BOOST_FOREACH(Label l, P[dest_node])
    {
        std::cout << "[" << l.cost[0] << ";" << l.cost[1] << "]" << std::endl;
    }*/
    return false;
}

// Algo de martins dans un graphe CH
// On maintient une liste de couts réalisables trouvés
// À la création d'un nouveau label, on vérifie qu'il n'est pas dominé par aucun label des couts réalisables
// À la visite d'un nœud dans un sens, si dans l'autre sens il a déjà été visité
// - pour chaque couple de labels (sens1/sens2), créer un nouveau label
// - s'il n'est dominé par aucun label dans la liste réalisable, le rajouter
bool ch_martins(Graph::node_t start_node, Graph::node_t dest_node, const Graph & g)
{  
    Graph::comps = 0;
    typedef Graph::node_t node_t;
    typedef Graph::edge_t edge_t;

    // Compte le nombre de labels visités
    int visited = 0;

    // Liste des chemins trouvés
    std::list<Label> found;

    //Les deux files de priorité
    my_queue::Type Q1, Q2;
    const  my_queue::by_cost cost_q1 = Q1.get<0>();
    const  my_queue::by_cost cost_q2 = Q2.get<0>();
    const  my_queue::by_nodes node_q1 = Q1.get<1>();
    const  my_queue::by_nodes node_q2 = Q2.get<1>();

    // Les deux listes de labels permanents
    std::vector< std::vector<Label> > P1(num_vertices(g.graph));
    std::vector< std::vector<Label> > P2(num_vertices(g.graph));

    Label start, dest;
    start.node = start_node;
    dest.node = dest_node;
    for(int i=0; i < Graph::objectives; i++)
    {
        start.cost[i] = 0;
        dest.cost[i] = 0;
    }

    Q1.insert(start);
    Q2.insert(dest);

    while(!Q1.empty() && !Q2.empty())
    {
        if(!Q1.empty())
        {
            Label l = *(cost_q1.begin());
            visited++;
            Q1.erase(cost_q1.begin());

            P1[l.node].push_back(l);
            //On regarde si on a réussi à construire un chemin non dominé
            BOOST_FOREACH(Label l2, P2[l.node])
            {
                Label new_label;
                for(int i=0; i < Graph::objectives; i++)
                    new_label.cost[i] = l2.cost[i] + l.cost[i];

                if(!is_dominated_by_any(found, new_label))
                {
                    found.remove_if(Label_dom(new_label));
                    found.push_back(new_label);
                }

            }


            BOOST_FOREACH(Graph::edge_t e, out_edges(l.node, g.foward))
            {
                Label l2;
                l2.node = boost::target(e, g.foward);
                BOOST_ASSERT(g.foward[l2.node].order != Graph::Node::undefined);

                for(int i=0; i < Graph::objectives; i++)
                    l2.cost[i] = l.cost[i] + g.foward[e].cost[i];

                if(!is_dominated_by_any(node_q1.equal_range(l2.node), l2) && !is_dominated_by_any(P1[l2.node],l2) && !is_dominated_by_any(found, l2))
                {
                    my_queue::nodes_it it, end;
                    tie(it, end) = node_q1.equal_range(l2.node);
                    while(it != end)
                    {
                        if(Graph::dominates(l2.cost, it->cost) || l2.cost == it->cost)
                            it = node_q1.erase(it);
                        else
                        {
                            it++;
                        }
                    }
                    Q1.insert(l2);
                }
            }
        }

        if(!Q2.empty())
        {
            Label l = *(cost_q2.begin());
            visited++;
            P2[l.node].push_back(l);
            Q2.erase(cost_q2.begin());

            //On regarde si on a réussi à construire un chemin non dominé
            BOOST_FOREACH(Label l2, P1[l.node])
            {
                Label new_label;
                for(int i=0; i < Graph::objectives; i++)
                    new_label.cost[i] = l2.cost[i] + l.cost[i];

                if(!is_dominated_by_any(found, new_label))
                {
                    found.remove_if(Label_dom(new_label));
                    found.push_back(new_label);
                }

            }


            BOOST_FOREACH(Graph::edge_t e, in_edges(l.node, g.backward))
            {
                Label l2;
                l2.node = boost::source(e, g.backward);

                for(int i=0; i < Graph::objectives; i++)
                    l2.cost[i] = l.cost[i] + g.backward[e].cost[i];

                if(!is_dominated_by_any(node_q2.equal_range(l2.node), l2) && !is_dominated_by_any(P2[l2.node],l2) && !is_dominated_by_any(found, l2))
                {
                    my_queue::nodes_it it, end;
                    tie(it, end) = node_q2.equal_range(l2.node);
                    while(it != end)
                    {
                        if(Graph::dominates(l2.cost, it->cost) || l2.cost == it->cost)
                            it = node_q2.erase(it);
                        else
                        {
                            it++;
                        }
                    }
                    Q2.insert(l2);
                }
            }
        }
    }

    std::cout << "Labels visited: " << visited << ", solutions found: " << found.size() << ", domination tests: " << Graph::comps << std::endl;
    /*   BOOST_FOREACH(Label l, found)
         {
         std::cout << "[" << l.cost[0] << ";" << l.cost[1] << "]" << std::endl;
         }
         */ return false;
}
// Algo de martins simplifié qui dit juste s'il existe un chemin dominant le coût passé en paramètre
bool martins_witness(Graph::node_t start_node, Graph::node_t dest_node, Graph::cost_t cost, const Graph::Type & g)
{
    my_queue::Type Q;
    Label start;
    start.node = start_node;
    for(int i=0; i < Graph::objectives; i++)
        start.cost[i] = 0;

    Q.insert(start);
    const  my_queue::by_cost cost_q_it = Q.get<0>();
    const  my_queue::by_nodes node_q = Q.get<1>();

    while( !Q.empty() )
    {
        Label l = *(cost_q_it.begin());
        Q.erase(cost_q_it.begin());
        if(l.node == dest_node && Graph::dominates(l.cost, cost))
            return true;
        BOOST_FOREACH(Graph::edge_t e, out_edges(l.node, g))
        {
            Label l2;
            l2.node = boost::target(e, g);
            for(int i=0; i < Graph::objectives; i++)
                l2.cost[i] = l.cost[i] + g[e].cost[i];

            if(!is_dominated_by_any(node_q.equal_range(l2.node), l2) && !Graph::dominates(cost, l2.cost) && cost != l2.cost)
            {
                my_queue::nodes_it it, end;
                tie(it, end) = node_q.equal_range(l2.node);
                while(it != end)
                {
                    if(Graph::dominates(l2.cost, it->cost) || l2.cost == it->cost)
                        it = Q.get<1>().erase(it);
                    else
                    {
                        it++;
                    }
                }
                Q.insert(l2);
            }
        }
    }

    return false;
}


