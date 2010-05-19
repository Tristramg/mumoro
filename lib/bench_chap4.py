import layer
import mumoro
import time
import random

#foot = layer.Layer('foot', mumoro.Foot, {'nodes': 'sf_nodes_ch4', 'edges': 'sf_edges_ch4'})
#bike = layer.Layer('bike', mumoro.Bike, {'nodes': 'sf_nodes_ch4', 'edges': 'sf_edges_ch4'})
#pt = layer.GTFSLayer('muni', 'pt2')

foot = layer.Layer('foot', mumoro.Foot, {'nodes': 'la_nodes_ch4', 'edges': 'la_edges_ch4'})
bike = layer.Layer('bike', mumoro.Bike, {'nodes': 'la_nodes_ch4', 'edges': 'la_edges_ch4'})
pt = layer.GTFSLayer('metro', 'la')



g = layer.MultimodalGraph([foot, pt, bike])

runs = 100
f = open('chap4_bench_la', 'w')
f.write('Modes Ville Algo Dist_Class Temps Visites\n')
random.seed(time.clock())

# Generate instances
nodes = {'A': [], 'B': [], 'C': [], 'D': [], 'E': []}
nodes_pt = {'A': [], 'B': [], 'C': [], 'D': []}

while len(nodes['A']) + len(nodes['B']) + len(nodes['C']) + len(nodes['D']) + len(nodes['E']) < runs * 5:
    s = random.randint(0, foot.count - 1)
    t = random.randint(0, foot.count - 1)
    
    d = g.graph.distance(s,t)
    if d < 3000 and len(nodes['A']) < runs:
        nodes['A'].append((d,s,t))
    elif d < 5000 and len(nodes['B']) < runs:
        nodes['B'].append((d,s,t))
    elif d < 10000 and len(nodes['C']) < runs:
        nodes['C'].append((d,s,t))
    elif d < 15000 and len(nodes['D']) < runs:
        nodes['D'].append((d,s,t))
    elif d < 20000 and len(nodes['E']) < runs:
        nodes['E'].append((d,s,t))

for (c, n) in nodes.items():
    print "{0} -> {1}".format(c, len(n))
print "First gen, done"

while len(nodes_pt['A']) + len(nodes_pt['B']) + len(nodes_pt['C']) + len(nodes_pt['D'])  < runs * 4:
    s = random.randint(0, pt.count - 1) + pt.offset
    t = random.randint(0, pt.count - 1) + pt.offset
    
    d = g.graph.distance(s,t)
    if d < 3000 and len(nodes_pt['A']) < runs:
        nodes_pt['A'].append((d,s,t))
    elif d < 5000 and len(nodes_pt['B']) < runs:
        nodes_pt['B'].append((d,s,t))

    elif d < 10000 and len(nodes_pt['C']) < runs:
        nodes_pt['C'].append((d,s,t))
    elif len(nodes_pt['D']) < runs:
        nodes_pt['D'].append((d,s,t))

for (c, n) in nodes_pt.items():
    print "{0} -> {1}".format(c, len(n))



print "Nodes generation done"

# Un seul mode
# TC

for (c, n) in nodes_pt.items():
    start = time.clock()
    vis = 0
    for p in n:
        vis += g.graph.dijkstra(p[1], p[2])
    end = time.clock()
    t = float(end - start)*1000/len(n)
    f.write('1 SF Dijkstra {0} {1} {2}\n'.format(c,t, vis/len(n)))

for (c, n) in nodes_pt.items():
    start = time.clock()
    vis = 0
    for p in n:
        vis += g.graph.astar(p[1], p[2])
    end = time.clock()
    t = float(end - start)*1000/len(n)
    f.write('1 SF astar {0} {1} {2}\n'.format(c,t, vis/len(n)))


for (c, n) in nodes.items():
    start = time.clock()
    vis = 0
    for p in n:
        vis += g.graph.dijkstra(p[1], p[2])
    end = time.clock()
    t = float(end - start)*1000/len(n)
    f.write('1b SF Dijkstra {0} {1} {2}\n'.format(c,t, vis/len(n)))

for (c, n) in nodes.items():
    start = time.clock()
    vis = 0
    for p in n:
        vis += g.graph.dijkstra_dist(p[1], p[2])
    end = time.clock()
    t = float(end - start)*1000/len(n)
    f.write('1c SF Dijkstra {0} {1} {2}\n'.format(c,t, vis/len(n)))


# Deux modes
# TC + marche
e = mumoro.Edge()
e.mode_change = 1
e.duration = mumoro.Duration(60);
e2 = mumoro.Edge()
e2.mode_change = 0
e2.duration = mumoro.Duration(30);
g.connect_nearest_nodes(pt, foot, e, e2)

for (c, n) in nodes.items():
    start = time.clock()
    vis = 0
    for p in n:
        vis += g.graph.dijkstra(p[1], p[2])
    end = time.clock()
    t = float(end - start)*1000/len(n)
    f.write('2 SF Dijkstra {0} {1} {2}\n'.format(c,t, vis/len(n)))

# Trois modes
# TC + marche + velib
# Distance
# Dijkstra court
# Dijkstra complet
# Astar


g.connect_nearest_nodes(bike, foot, e)
for (c, n) in nodes.items():
    start = time.clock()
    vis = 0
    for p in n:
        vis += g.graph.dijkstra(p[1] + bike.offset, p[2])
    end = time.clock()
    t = float(end - start)*1000/len(n)
    f.write('3 SF Dijkstra {0} {1} {2}\n'.format(c,t, vis/len(n)))


for (c, n) in nodes.items():
    start = time.clock()
    vis = 0
    for p in n:
        vis += g.graph.dijkstra(p[1] + bike.offset)
    end = time.clock()
    t = float(end - start)*1000/len(n)
    f.write('3 SF Dijkstra_full {0} {1} {2}\n'.format(c,t, vis/len(n)))

for (c, n) in nodes.items():
    start = time.clock()
    vis = 0
    for p in n:
        vis += g.graph.astar(p[1] + bike.offset, p[2])
    end = time.clock()
    t = float(end - start)*1000/len(n)
    f.write('3 SF Astar {0} {1} {2}\n'.format(c,t, vis/len(n)))


