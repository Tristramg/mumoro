ch: main.o bench.o test.o dijkstra.o contraction.o query.o
	g++ -o ch main.o bench.o test.o dijkstra.o contraction.o query.o -lpqxx -Wall -lboost_serialization

main.o: main.cc
	g++ -O3 -Wall -o main.o -c main.cc

bench.o: bench.cc
	g++ -g -Wall -o bench.o -c bench.cc

test.o: test.cc
	g++ -O3 -Wall -o test.o -c test.cc

dijkstra.o: dijkstra.cc
	g++ -O3 -Wall -o dijkstra.o -c dijkstra.cc

contraction.o: contraction.cc
	g++ -O3 -Wall -o contraction.o -c contraction.cc

query.o: query.cc
	g++ -O3 -Wall -o query.o -c query.cc
