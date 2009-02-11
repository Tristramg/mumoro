#include "shortest_path.h"
using namespace Mumoro;
int main(int argc, char ** argv)
{
    Shortest_path p;
    Layer foot = p.add_layer("toulouse2.mum", Foot, false);
    std::cout << "Read the first layer" << std::endl;

    Layer sub = p.add_layer("toulouse2.mum", Subway, false);
    std::cout << "Read the subway layer " << std::endl;

    Layer velouse = p.add_layer(argv[1], Bike, false);
    std::cout << "Added the cycling layer " << std::endl;

    p.connect(foot, sub, FunctionPtr(new Const_cost(200)),  FunctionPtr( new Const_cost(60) ), argv[1], "metroA" );
    p.connect(foot, velouse, FunctionPtr(new Const_cost(60)),  FunctionPtr( new Const_cost(30) ), argv[1], "velouse" );
    std::cout << "Connected both layers" << std::endl;

    p.build();
   
   int max = foot.cnt(); 
   clock_t start,finish;
   double time;
   srand(30984);
   double sum = 0;
   double maxt = 0;
   int i;
   for(i = 0; i<100; i++)
   {
       int startn = rand() % max;
       start = clock();
       p.compute(startn,0);
       finish = clock();
       time =  ((double(finish)-double(start))*1000)/CLOCKS_PER_SEC;
       sum += time;
       if(time > maxt)
           maxt = time;
   }

   std::cout << "Nodes = " << foot.cnt() << std::endl;
   std::cout << "Avg = " << sum / i << std::endl;
   std::cout << "Worse = " << maxt << std::endl;

   return 0;
}
