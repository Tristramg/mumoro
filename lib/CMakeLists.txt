CMAKE_MINimum_required(VERSION 2.6)

SET( CMAKE_BUILD_TYPE DEBUG )

FIND_LIBRARY(PQXX pqxx)
FIND_LIBRARY(BOOST boost_graph)

ADD_DEFINITIONS( -Wall -Wno-deprecated)


ADD_EXECUTABLE(mum_test main.cpp MultimodalGraph.cpp martins.cpp tsaggouris.cpp )
TARGET_LINK_LIBRARIES(mum_test ${PQXX} )

