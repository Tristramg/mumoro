CMAKE_MINimum_required(VERSION 2.6)

SET( CMAKE_BUILD_TYPE DEBUG )

FIND_LIBRARY(PQXX pqxx)
FIND_LIBRARY(BOOST_GRAPH boost_graph)

ADD_DEFINITIONS( -g -Wall -Wno-deprecated)

ADD_LIBRARY(mum_lib MultimodalGraph.cpp martins.cpp tsaggouris.cpp) 
TARGET_LINK_LIBRARIES(mum_lib ${PQXX} )

ADD_EXECUTABLE(mum_test main.cpp )
TARGET_LINK_LIBRARIES(mum_test mum_lib)

FIND_LIBRARY(BOOST_REGEX boost_regex)
FIND_LIBRARY(FCGI fcgi)

ADD_EXECUTABLE(mum.fcgi fcgi.cpp )
TARGET_LINK_LIBRARIES(mum.fcgi mum_lib ${BOOST_REGEX} ${FCGI} )

ADD_EXECUTABLE(match.fcgi matcher.cpp )
TARGET_LINK_LIBRARIES(match.fcgi ${PQXX} ${BOOST_REGEX} ${FCGI} )
