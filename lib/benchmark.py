import layer
import mumoro
import time
import random

foot = layer.Layer('foot', mumoro.Foot, {'nodes': 'sf_nodes_ch4', 'edges': 'sf_edges_ch4'})
bike = layer.Layer('bike', mumoro.Bike, {'nodes': 'sf_nodes_ch4', 'edges': 'sf_edges_ch4'})
pt = layer.GTFSLayer('muni', 'pt2')
g = layer.MultimodalGraph([foot, pt, bike])

e = mumoro.Edge()
e.mode_change = 1
e.duration = mumoro.Duration(60);
e2 = mumoro.Edge()
e2.mode_change = 0
e2.duration = mumoro.Duration(30);
g.connect_nearest_nodes(pt, foot, e, e2)

g.connect_nearest_nodes(bike, foot, e)
#g.connect_nearest_nodes(bike, pt, e)

random.seed(time.clock())
found = 0
comp = []
runs = 2

found = 0

for x in range(runs):
    s = random.randint(0, bike.count - 1) + bike.offset
    t = random.randint(0, foot.count - 1)
    comp.append((s,t))



found = 0
start = time.clock()
for (s,t) in comp:
    p = mumoro.martins(s, t, g.graph, 30000, mumoro.mode_change)
    found += len(p)
end = time.clock()
efound = 0
estart = time.clock()
for (s,t) in comp:
    p = mumoro.relaxed_martins(s, t, g.graph, 30000, mumoro.mode_change, 120)
    efound += len(p)
eend = time.clock()
fstart = time.clock()
for (s,t) in comp:
    p = mumoro.relaxed_martins(s, -1, g.graph, 30000, mumoro.mode_change, 120)
fend = time.clock()
print "\"t + ms\" {0} {1} {2} {3} ".format(float(found)/runs, float(end - start) * 1000 / runs, float(efound)/runs, float(eend - estart) * 1000 / runs)


found = 0
start = time.clock()
for (s,t) in comp:
    p = mumoro.martins(s, t, g.graph, 30000, mumoro.mode_change, mumoro.line_change)
    found += len(p)
end = time.clock()
efound = 0
estart = time.clock()
for (s,t) in comp:
    p = mumoro.relaxed_martins(s, t, g.graph, 30000, mumoro.mode_change, 120, mumoro.line_change, 60)
    efound += len(p)
eend = time.clock()
print "\"t + ms + ls\" {0} {1} {2} {3}".format(float(found)/runs, float(end - start) * 1000 / runs, float(efound)/runs, float(eend - estart) * 1000 / runs)


found = 0
start = time.clock()
for (s,t) in comp:
    p = mumoro.martins(s, t, g.graph, 30000, mumoro.elevation)
    found += len(p)
end = time.clock()
efound = 0
estart = time.clock()
for (s,t) in comp:
    p = mumoro.relaxed_martins(s, t, g.graph, 30000, mumoro.elevation, 10)
    efound += len(p)
eend = time.clock()
print "\"t + a\" {0} {1} {2} {3}".format(float(found)/runs, float(end - start) * 1000 / runs, float(efound)/runs, float(eend - estart) * 1000 / runs)


found = 0
start = time.clock()
for (s,t) in comp:
    p = mumoro.martins(s, t, g.graph, 30000, mumoro.elevation, mumoro.line_change, mumoro.mode_change)
    found += len(p)
end = time.clock()
efound = 0
estart = time.clock()
for (s,t) in comp:
    p = mumoro.relaxed_martins(s, t, g.graph, 30000, mumoro.elevation, 10, mumoro.line_change, 60, mumoro.mode_change, 120)
    efound += len(p)
eend = time.clock()
print "\"t + a + ms + ls\" {0} {1} {2} {3}".format(float(found)/runs, float(end - start) * 1000 / runs, float(efound)/runs, float(eend - estart) * 1000 / runs)


