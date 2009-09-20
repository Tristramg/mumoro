#include "martins_impl.h"

vector<Path> martins(node_t start_node, node_t dest_node, MultimodalGraph & g, int start_time)
{
    vector<float Edge::*> objectives;
    return martins<1>(start_node, dest_node, g, start_time, objectives, Dominates<1>());
}

vector<Path> martins(node_t start_node, node_t dest_node, MultimodalGraph & g, float Edge::*obj2, int start_time)
{
    vector<float Edge::*> objectives;
    objectives.push_back(obj2);
    return martins<2>(start_node, dest_node, g, start_time, objectives, Dominates<2>());
}

vector<Path> martins(node_t start_node, node_t dest_node, MultimodalGraph & g, float Edge::*obj2, float Edge::*obj3, int start_time)
{
    vector<float Edge::*> objectives;
    objectives.push_back(obj2);
    objectives.push_back(obj3);
    return martins<3>(start_node, dest_node, g, start_time, objectives, Dominates<3>());
}


vector<Path> martins(node_t start_node, node_t dest_node, MultimodalGraph & g, float Edge::*obj2, float Edge::*obj3, float Edge::*obj4, int start_time)
{
    vector<float Edge::*> objectives;
    objectives.push_back(obj2);
    objectives.push_back(obj3);
    objectives.push_back(obj4);
    return martins<4>(start_node, dest_node, g, start_time, objectives, Dominates<4>());
}

vector<Path> relaxed_martins(node_t start_node, node_t dest_node, MultimodalGraph & g, float Edge::*obj2, float Edge::*obj3, int start_time)
{
    vector<float Edge::*> objectives;
    objectives.push_back(obj2);
    objectives.push_back(obj3);
    return martins<3>(start_node, dest_node, g, start_time, objectives, Relaxed_dominates<3>());
}

float delta(float a, float b)
{
    return a < b ? b - a : b - a;
}
