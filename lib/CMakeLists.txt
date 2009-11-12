CMAKE_MINimum_required(VERSION 2.6)

SET( CMAKE_BUILD_TYPE DEBUG )

FIND_LIBRARY(PQXX pqxx /opt/local/lib)
find_package(Boost COMPONENTS system regex graph REQUIRED)

include_directories(${Boost_INCLUDE_DIRS})

ADD_DEFINITIONS( -g -Wall -Wno-deprecated)

ADD_LIBRARY(mum_lib MultimodalGraph.cpp martins.cpp tsaggouris.cpp) 
TARGET_LINK_LIBRARIES(mum_lib ${PQXX} )

ADD_EXECUTABLE(mum_test main.cpp )
TARGET_LINK_LIBRARIES(mum_test mum_lib)

FIND_LIBRARY(FCGI fcgi)

ADD_EXECUTABLE(mum.fcgi fcgi.cpp )
TARGET_LINK_LIBRARIES(mum.fcgi mum_lib ${Boost_LIBRARIES} ${FCGI} )

ADD_EXECUTABLE(match.fcgi matcher.cpp )
TARGET_LINK_LIBRARIES(match.fcgi ${PQXX} ${Boost_LIBRARIES} ${FCGI} )
