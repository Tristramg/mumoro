import layer
import mumoro
import time
import random
import signal

runs = 10
timeout = 30

class TimeoutFunctionException(Exception): 
    pass 

def handle_timeout(signum, frame): 
    raise TimeoutFunctionException()




#foot = layer.Layer('foot', mumoro.Foot, {'nodes': 'sf_nodes_ch4', 'edges': 'sf_edges_ch4'})
#bike = layer.Layer('bike', mumoro.Bike, {'nodes': 'sf_nodes_ch4', 'edges': 'sf_edges_ch4'})
#pt = layer.GTFSLayer('muni', 'pt2')

foot = layer.Layer('foot', mumoro.Foot, {'nodes': 'la_nodes_ch4', 'edges': 'la_edges_ch4'})
bike = layer.Layer('bike', mumoro.Bike, {'nodes': 'la_nodes_ch4', 'edges': 'la_edges_ch4'})
pt = layer.GTFSLayer('metro', 'la')

g = layer.MultimodalGraph([foot, pt, bike])

e = mumoro.Edge()
e.mode_change = 1
e.duration = mumoro.Duration(60);
e2 = mumoro.Edge()
e2.mode_change = 0
e2.duration = mumoro.Duration(30);
g.connect_nearest_nodes(pt, foot, e, e2)

#e.mode_change = 0
g.connect_nearest_nodes(pt, bike, None, e)

#g.connect_same_nodes(bike, foot, e)

random.seed(time.time())


# Generate instances
nodes = {'A': [], 'B': [], 'C': [], 'D': [], 'E': []}

while len(nodes['A']) + len(nodes['B']) + len(nodes['C']) + len(nodes['D']) + len(nodes['E']) < runs * 5:
    s = random.randint(0, bike.count - 1) + bike.offset
    t = random.randint(0, foot.count - 1)
    
    d = g.graph.distance(s,t)
    if d < 3000:
        if len(nodes['A']) < runs:
            nodes['A'].append((d,s,t))
    elif d < 5000:
        if len(nodes['B']) < runs:
            nodes['B'].append((d,s,t))
    elif d < 10000:
        if len(nodes['C']) < runs:
            nodes['C'].append((d,s,t))
    elif d < 15000:
        if len(nodes['D']) < runs:
            nodes['D'].append((d,s,t))
    elif d < 20000:
        if len(nodes['E']) < runs:
            nodes['E'].append((d,s,t))


def bench(nodes, f, *args):
    start = time.time()
    found = 0
    for n in nodes:
        s = n[1]
        t = n[2]
        p = f(s, t, g.graph, 30000, *args)
            #p = mumoro.martins(s, t, g.graph, 30000, mumoro.elevation)
        found += len(p)
        if time.time() - start > runs * timeout:
            return (0, 0)
    tps = 1000 * float(time.time() - start)/runs
    sol = float(found)/runs
    return (tps, sol)

f = open('chap5_bench', 'w')
f.write('Objectifs Heuristique Temps Solutions Classe\n')

f.flush()

for (c,n) in nodes.items():
    print "New set : {0}".format(c)

    print "TE"
    re = bench(n, mumoro.relaxed_martins, mumoro.elevation, 10)
    f.write('"te" "Dominance rel." {0} {1} {2}\n'.format(re[0], re[1],c))
    r = bench(n, mumoro.martins, mumoro.elevation)
    f.write('"te" Optimal {0} {1} {2}\n'.format(r[0], r[1],c))
    f.flush()

    print "TM"
    re = bench(n, mumoro.relaxed_martins, mumoro.mode_change, 120)
    f.write('"tm" "Dominance rel." {0} {1} {2}\n'.format(re[0], re[1],c))
    r = bench(n, mumoro.martins, mumoro.mode_change)
    f.write('"tm" Optimal {0} {1} {2}\n'.format(r[0], r[1],c))
    f.flush()

    print "TML"
    re = bench(n, mumoro.relaxed_martins, mumoro.mode_change, 120, mumoro.line_change, 60)
    f.write('"tml" "Dominance rel." {0} {1} {2}\n'.format(re[0], re[1],c))
    r = bench(n, mumoro.martins, mumoro.mode_change, mumoro.line_change)
    f.write('"tml" Optimal {0} {1} {2}\n'.format(r[0], r[1],c))
    f.flush()

    print "TEML"
    re = bench(n, mumoro.relaxed_martins, mumoro.mode_change, 120, mumoro.line_change, 60, mumoro.elevation, 10)
    f.write('"teml" "Dominance rel." {0} {1} {2}\n'.format(re[0], re[1],c))
    r = bench(n, mumoro.martins, mumoro.mode_change, mumoro.line_change, mumoro.elevation)
    f.write('"teml" Optimal {0} {1} {2}\n'.format(r[0], r[1],c))
    f.flush()

#    print "TC"
#    re = bench(n, mumoro.relaxed_martins, mumoro.co2, 0.1)
#    f.write('"teml" "Dominance rel." {0} {1} {2}\n'.format(re[0], re[1],c))
#    r = bench(n, mumoro.martins, mumoro.co2)
#    f.write('"tc" {0} {1} {2} {3} {4}\n'.format(r[0], r[1], re[0], re[1],c))
#    f.flush()


