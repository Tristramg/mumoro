FIND_PACKAGE(Boost REQUIRED)
FIND_LIBRARY(SQL sqlite3 REQUIRED)
SET( CMAKE_BUILD_TYPE DEBUG )


SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -Wall -pedantic -Wno-long-long")

SET(LIB_FILES shortest_path.cc)
ADD_LIBRARY(shortestpath ${LIB_FILES})
ADD_EXECUTABLE(test test.cc)
TARGET_LINK_LIBRARIES(test shortestpath ${SQL})


