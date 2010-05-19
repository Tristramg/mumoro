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




foot = layer.Layer('foot', mumoro.Foot, {'nodes': 'sf_nodes_ch4', 'edges': 'sf_edges_ch4'})
bike = layer.Layer('bike', mumoro.Bike, {'nodes': 'sf_nodes_ch4', 'edges': 'sf_edges_ch4'})
#pt = layer.GTFSLayer('muni', 'pt2')

#foot = layer.Layer('foot', mumoro.Foot, {'nodes': 'la_nodes_ch4', 'edges': 'la_edges_ch4'})
#bike = layer.Layer('bike', mumoro.Bike, {'nodes': 'la_nodes_ch4', 'edges': 'la_edges_ch4'})

g1 = layer.MultimodalGraph([foot, bike])
#g2 = layer.MultimodalGraph([foot, bike])
#g3 = layer.MultimodalGraph([foot, bike])
#g4 = layer.MultimodalGraph([foot, bike])

e = mumoro.Edge()
e.mode_change = 1
e.duration = mumoro.Duration(60);

g1.connect_same_nodes(bike, foot, e)
#g2.connect_same_nodes_random(bike, foot, e, 10)
#g3.connect_same_nodes_random(bike, foot, e, 100)
#g4.connect_same_nodes_random(bike, foot, e, 1000)

random.seed(time.time())


# Generate instances
nodes = {'A': [], 'B': [], 'C': [], 'D': [], 'E': []}

while len(nodes['A']) + len(nodes['B']) + len(nodes['C']) + len(nodes['D']) < runs * 4:
    s = random.randint(0, bike.count - 1) + bike.offset
    t = random.randint(0, foot.count - 1)
    
    d = g1.graph.distance(s,t)
    print len(nodes['A']), len(nodes['B']), len(nodes['C']), len(nodes['D']), d
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

def bench(g, nodes, f, *args):
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

f = open('chap6_bench', 'w')
f.write('Objectifs Heuristique Temps Solutions Classe\n')

f.flush()

for (c,n) in nodes.items():
    print "New set : {0}".format(c)

    print "1/1"
    r = bench(g1, n, mumoro.martins, mumoro.elevation)
    f.write('"te" "1/1" {0} {1} {2}\n'.format(r[0], r[1],c))
    f.flush()

    print "1/10"
    r = bench(g2, n, mumoro.martins, mumoro.elevation)
    f.write('"te" "1/10" {0} {1} {2}\n'.format(r[0], r[1],c))
    f.flush()

    print "1/100"
    r = bench(g3, n, mumoro.martins, mumoro.elevation)
    f.write('"te" "1/100" {0} {1} {2}\n'.format(r[0], r[1],c))
    f.flush()

    print "1/1000"
    r = bench(g4, n, mumoro.martins, mumoro.elevation)
    f.write('"te" "1/1000" {0} {1} {2}\n'.format(r[0], r[1],c))
    f.flush()

