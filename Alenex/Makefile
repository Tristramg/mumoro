CXX=g++
CXXFLAGS=-W -Wall -ansi -pedantic -O3 -Wno-deprecated
EXEC=alenex_experiments

all: $(EXEC)

alenex_experiments: main.o martins.o multimodal_graph.o
	$(CXX) -o $@ $^ $(LDFLAGS)

multimodal_graph.o: MultimodalGraph.cpp MultimodalGraph.h
	$(CXX) -o $@ -c $< $(CXXFLAGS)

main.o: main.cpp martins.h MultimodalGraph.h
	$(CXX) -o $@ -c $< $(CXXFLAGS)

martins.o: martins.cpp martins_impl.h martins.h MultimodalGraph.h
	$(CXX) -o $@ -c $< $(CXXFLAGS)

clean:
	rm  *.o

mrproper: clean
	rm $(EXEC)

