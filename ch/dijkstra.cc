#include "dijkstra.h"

//Foncteur annexe qui retourne vrai si le 1er nœud a une distance plus petite
using namespace boost;
struct Compare
{
    const std::vector<float> & vec;
    Compare(const std::vector<float> & dist) : vec(dist) {}
    bool operator()(int a, int b) const
    {
        return vec[a] < vec[b];
    }
};


enum Color {White=0, Gray, Black};

//Simple fonction pour tester si le calcul du plus court chemin fonctionne
//On retourne que la distance pour comparer par rapport à du dijkstra
float query_mono(Graph::node_t start, Graph::node_t dest, const Graph::Type & graph)
{
    typedef Graph::node_t node_t;
    typedef Graph::edge_t edge_t;

    typedef color_traits<two_bit_color_type> Color;
    float best_distance = std::numeric_limits<float>::max();
    //Vecteurs de distance
    std::vector<float> dist1(boost::num_vertices(graph), std::numeric_limits<float>::max());
    std::vector<float> dist2(boost::num_vertices(graph), std::numeric_limits<float>::max());

    //Les deux files de priorité
    boost::relaxed_heap<node_t, Compare > queue1(boost::num_vertices(graph), Compare(dist1));
    boost::relaxed_heap<node_t, Compare > queue2(boost::num_vertices(graph), Compare(dist2));


    // L'utilisation de ce color map, permet de gratter 10% sur un test
    boost::two_bit_color_map<> col1(boost::num_vertices(graph));
    boost::two_bit_color_map<> col2(boost::num_vertices(graph));

    dist1[start] = 0;
    put(col1, start, Color::gray());
    queue1.push(start);

    dist2[dest] = 0;
    put(col2, dest, Color::gray());
    queue2.push(dest);

    float min1 = 0;
    float min2 = 0;
    int visited = 0;

    while(min1 < best_distance && min2 < best_distance && (!queue1.empty() || !queue2.empty()))
    {
        if(!queue1.empty() && min2 < best_distance)
        {
            //On prend le plus petit nœud gris
            node_t n1 = queue1.top();
            queue1.pop();
            visited++;
            put(col1, n1, Color::black());
            min1 = dist1[n1];
            //Pour tous ses successeurs
            BOOST_FOREACH(edge_t edge, boost::out_edges(n1, graph))
            {
                node_t v = boost::target(edge, graph);
                //On ne prend que les nœuds plus grands
                if(graph[v].order >= graph[n1].order)
                {
                    //Si on a trouvé plus court vers le successeurs
                    if(min1 + graph[edge].cost0 < dist1[v])
                    {
                        dist1[v] = min1 + graph[edge].cost0;
                        //Si on avait jamais visité ce nœud, on le rajoute à la queue
                        if(get(col1,v) == Color::white())
                        {
                            put(col1,v, Color::gray());
                            queue1.push(v);
                        }
                        else// if(get(col1,v) == Color::gray())
                        {
                            queue1.update(v);
                        }
                    }
                }
                //On fait un check des fois que le nœud ait déjà été atteint
                // dans l'autre sens
                if(dist1[v] + dist2[v] < best_distance)
                {
                    best_distance = dist1[v] + dist2[v];
                }
            }
        }

        // HOP ! Copier-coller pour avoir l'algo qui tourne dans l'autre sens
        if(!queue2.empty() && min2 < best_distance)
        {
            //On prend le plus petit nœud gris
            node_t n2 = queue2.top(); queue2.pop();
            visited++;
            min2 = dist2[n2];
            //Pour tous ses successeurs
            BOOST_FOREACH(edge_t edge, boost::in_edges(n2, graph))
            {
                node_t v = boost::source(edge, graph);
                //On ne prend que les nœuds plus grands
                if(graph[v].order >= graph[n2].order)
                {
                    //Si on a trouvé plus court vers le successeurs
                    if(min2 + graph[edge].cost0 < dist2[v])
                    {
                        dist2[v] = min2 + graph[edge].cost0;
                        //Si on avait jamais visité ce nœud, on le rajoute à la queue
                        if(get(col2,v) == Color::white())
                        {
                            put(col2,v, Color::gray());
                            queue2.push(v);
                        }
                        else// if(get(col2,v) == Color::gray())
                        {
                            queue2.update(v);
                        }
                    }
                }
                //On fait un check des fois que le nœud ait déjà été atteint
                if(dist1[v] + dist2[v] < best_distance)
                {
                    best_distance = dist1[v] + dist2[v];
                }
            }
            put(col2,n2, Color::black());
        }
    }
    std::cout << "Contractions visited " << visited << std::endl;
    return best_distance;
}

