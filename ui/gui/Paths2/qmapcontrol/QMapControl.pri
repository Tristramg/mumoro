DEPENDPATH += src
INCLUDEPATH += src
MOC_DIR = tmp
OBJECTS_DIR = obj

# Input
HEADERS += curve.h \
           geometry.h \
           imagemanager.h \
           layer.h \
           layermanager.h \
           linestring.h \
           mapadapter.h \
           mapcontrol.h \
           mapnetwork.h \
           point.h \
           tilemapadapter.h \
           circlepoint.h \
           imagepoint.h \
           gps_position.h \
           osmmapadapter.h \
           maplayer.h \
           geometrylayer.h \
           fixedimageoverlay.h
SOURCES += curve.cpp \
           geometry.cpp \
           imagemanager.cpp \
           layer.cpp \
           layermanager.cpp \
           linestring.cpp \
           mapadapter.cpp \
           mapcontrol.cpp \
           mapnetwork.cpp \
           point.cpp \
           tilemapadapter.cpp \
           circlepoint.cpp \
           imagepoint.cpp \
           gps_position.cpp \
           osmmapadapter.cpp \
           maplayer.cpp \
           geometrylayer.cpp \
           fixedimageoverlay.cpp

QT += network
