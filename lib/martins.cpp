#include "martins_impl.h"
#include "martins.h"
vector<Path> martins(int start_node, int dest_node, Graph & g, int start_time)
{
    vector<float Edge::*> objectives;
    return martins<1>(start_node, dest_node, g, start_time, objectives, Dominates<1>());
}

vector<Path> martins_py(int start_node, int dest_node, Graph & g)
{
    vector<float Edge::*> objectives;
    objectives.push_back(&Edge::mode_change);
    objectives.push_back(&Edge::line_change);
    return martins<3>(start_node, dest_node, g, 30000, objectives, Dominates<3>());
}
vector<Path> martins(int start_node, int dest_node, Graph & g, float Edge::*obj2, int start_time)
{
    vector<float Edge::*> objectives;
    objectives.push_back(obj2);
    return martins<2>(start_node, dest_node, g, start_time, objectives, Dominates<2>());
}

vector<Path> martins(int start_node, int dest_node, Graph & g, float Edge::*obj2, float Edge::*obj3, int start_time)
{
    vector<float Edge::*> objectives;
    objectives.push_back(obj2);
    objectives.push_back(obj3);
    return martins<3>(start_node, dest_node, g, start_time, objectives, Dominates<3>());
}


vector<Path> martins(int start_node, int dest_node, Graph & g, float Edge::*obj2, float Edge::*obj3, float Edge::*obj4, int start_time)
{
    vector<float Edge::*> objectives;
    objectives.push_back(obj2);
    objectives.push_back(obj3);
    objectives.push_back(obj4);
    return martins<4>(start_node, dest_node, g, start_time, objectives, Dominates<4>());
}

vector<Path> relaxed_martins(int start_node, int dest_node, Graph & g, float Edge::*obj2, float Edge::*obj3, int start_time)
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
