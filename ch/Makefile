ch: main.o bench.o test.o
	g++ -o ch main.o bench.o test.o -lpqxx -Wall -lboost_serialization

main.o: main.cc
	g++ -O3 -Wall -o main.o -c main.cc

bench.o: bench.cc
	g++ -O3 -Wall -o bench.o -c bench.cc

test.o: test.cc
	g++ -O3 -Wall -o test.o -c test.cc

