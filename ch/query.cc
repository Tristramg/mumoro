#include "query.h"
// Décrit une étiquette (label) utilisée pendant l'exploration
// Cela représente un état de l'exploration et un chemin possible
struct Label
{
    Graph::cost_t cost; // coût du chemin
    Graph::node_t node; // nœud destination du chemin
    boost::shared_ptr<Label> predecessor;
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
        if( Graph::dominates(a.cost, l.cost) || a.cost == l.cost)
        {
    //        std::cout << "Domination: " << a.node << "<" << l.node << " [" << a.cost[0] << "," << a.cost[1] << "] < [" << l.cost[0] << "," << l.cost[1] << "]" << std::endl;
            return true;
        }
    }
    return false;
}

// Algo de martins sur le graphe normal
bool martins(Graph::node_t start_node, const Graph & g)
{
    my_queue::Type Q;
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

            if(!is_dominated_by_any(node_q.equal_range(l2.node), l2) && !is_dominated_by_any(P[l2.node],l2))
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
              //  std::cout << "    ins node=" << l2.node << " [" << l2.cost[0] << "," << l2.cost[1] << "]" << std::endl;
            }
        }
    }
    float labels = 0;
    BOOST_FOREACH(Graph::node_t n, boost::vertices(g.graph))
    {
        labels += P[n].size();
    }

    std::cout << "Labels visited: " << visited << ", solutions found: " << labels << std::endl;
    return false;
}



