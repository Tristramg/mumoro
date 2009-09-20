/*
    This file is part of Mumoro.

    Mumoro is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Mumoro is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Mumoro.  If not, see <http://www.gnu.org/licenses/>.
*/
#include <QtGui/QMainWindow>
#include <QtGui/QApplication>
#include <QtCore/QDebug>
#include <QVBoxLayout>
#include <QPushButton>
#include <QRadioButton>
#include "marble/GeoPainter.h"
#include "marble/MarbleWidget.h"
#include "marble/GeoDataPoint.h"
#include "marble/GeoDataLineString.h"
#include "object.h"
#include <QDockWidget>
#include <QLabel>
using namespace Marble;
using namespace Mumoro;


MyMarble::MyMarble(QWidget * w) :
    MarbleWidget(w), start_defined(false), end_defined(false) {}

    void  MyMarble::customPaint( GeoPainter *painter ){

        painter->setPen( QColor( 99, 99, 0 ) );

        QRadialGradient radialGrad(QPointF(100, 100), 100);
        radialGrad.setColorAt(0, QColor( 198, 198, 198, 200 ) );
        radialGrad.setColorAt(0.5, QColor( 199, 198, 99, 200 ) );
        radialGrad.setColorAt( 1, Qt::white );
        radialGrad.setSpread( QGradient::ReflectSpread );

        QBrush gradientBrush( radialGrad );
        painter->setBrush( gradientBrush );

        if ( start_defined )
        {
            GeoDataPoint s(start.lon, start.lat, 0.0, GeoDataPoint::Degree );
            painter->drawAnnotation (s, "Start", QSize(80, 50), 10, 30, 15, 15 );
        }
        if( end_defined )
        {
            GeoDataPoint s(end.lon, end.lat, 0.0, GeoDataPoint::Degree );
            painter->drawAnnotation (s, "End", QSize(80, 50), 10, 30, 15, 15 );
        }

        QPen pen;
        pen.setWidth(3);
        std::list<Mumoro::Path_elt>::const_iterator i = path.begin();
        for(i = path.begin(); i != path.end(); i++)
        {
            if( (*i).mode == Mumoro::Bike )
                pen.setColor( QColor( 255, 0, 0 ) );
            if( (*i).mode == Mumoro::Foot )
                pen.setColor( QColor( 0, 255, 0 ) );
            if( (*i).mode == Mumoro::Subway )
                pen.setColor( QColor( 255, 0, 255 ) );
            if( (*i).mode == Mumoro::Switch )
                pen.setColor( QColor( 0, 0, 255 ) );

            painter->setPen(pen);
            painter->drawLine(
                    GeoDataPoint((*i).source.lon, (*i).source.lat, 0, GeoDataCoordinates::Degree),
                    GeoDataPoint((*i).target.lon, (*i).target.lat, 0, GeoDataCoordinates::Degree) );
        }
    }


void MyMarble::mouseClickGeoPosition(qreal lon ,qreal lat,GeoDataCoordinates::Unit )
{
    if(click_action > 0)
    {
        qreal lon_d = lon * 180 / M_PI;
        qreal lat_d = lat * 180 / M_PI;
        if ( click_action == SEL_START )
        {
            try
            {
            start = p.match(lon_d, lat_d);
            start_defined = true;
            }
            catch( Node_not_found )
            {
                start_defined = false;
            }
        }
        else if ( click_action == SEL_DEST )
        {
            try
            {
                end = p.match(lon_d, lat_d);
                end_defined = true;
            }
            catch( Node_not_found )
            {
                end_defined = false;
            }
        }

        if(start_defined && end_defined)
        {        
            
            qDebug() << "start" << start.id<<start.lon<<start.lon;
            qDebug() << "end" << end.id<<end.lon<<end.lon;
            path = p.compute(start.id, end.id);
            std::cout << p.compute_xml(start.id, end.id);
            qDebug() << "Computed path of size: " << path.size();
        }
    }
    emit info_string(gen_info());
 }

QString MyMarble::gen_info()
{
    QString str("<center><b>Informations<b></center>\n");
    str.append("<b>Start node:</b> %1<br>");
    str=(start_defined ? str.arg(start.id) : str.arg("unknown")) ;

    str.append("<b>End node:</b> %1<br><br>");
    str=(end_defined ? str.arg(end.id) : str.arg("unknown"));
    return str;
}

void MyMarble::setStart()
{
    click_action = SEL_START;
}

void MyMarble::setEnd()
{
    click_action = SEL_DEST;
}

void MyMarble::setNav()
{
    click_action = NAV;   
}

int main( int argc, char *argv[] )
{
    if (argc < 2)
    {
        std::cout << "Usage: " << argv[0] << " database" << std::endl;
        exit(0);
    }

    QApplication a( argc, argv );
    QMainWindow w;
    QDockWidget dock( "Path calculation");
    w.addDockWidget(Qt::LeftDockWidgetArea, &dock);


    QWidget widg;
    QRadioButton start( "Set &start" );
    QRadioButton destination( "Set &destination" );
    QPushButton quit( "&Quit" );
    QRadioButton nav( "&Navigate" );

    QLabel info;

    QVBoxLayout left;
    left.addWidget( &nav );
    left.addWidget( &start );
    left.addWidget( &destination );
    left.addWidget( &info );
    left.addStretch();
    left.addWidget( &quit );
    widg.setLayout( &left );
    dock.setWidget(&widg);

    MyMarble foo;
    foo.setMapThemeId( "earth/openstreetmap/openstreetmap.dgml" );
    foo.setDownloadUrl("http://download.kde.org/apps/marble/");
    foo.setShowOverviewMap( false );
    foo.setShowCompass( false );

        Layer foot = foo.p.add_layer(argv[1], Foot, false);
        std::cout << "Read the first layer" << std::endl;

        Layer sub = foo.p.add_layer(argv[1], Subway, false);
        std::cout << "Read the subway layer " << std::endl;

        Layer velouse = foo.p.add_layer(argv[1], Bike, false);
        std::cout << "Added the cycling layer " << std::endl;

        foo.p.connect(foot, sub, FunctionPtr(new Const_cost(200)),  FunctionPtr( new Const_cost(60) ), argv[1], "metroA" );
        foo.p.connect(foot, velouse, FunctionPtr(new Const_cost(60)),  FunctionPtr( new Const_cost(30) ), argv[1], "velouse" );
        std::cout << "Connected both layers" << std::endl;

        foo.p.build();



    foo.enableInput();

    info.setText(foo.gen_info());

    QObject::connect(&foo, SIGNAL(mouseClickGeoPosition(qreal, qreal,GeoDataCoordinates::Unit)),
            &foo, SLOT(mouseClickGeoPosition(qreal, qreal,GeoDataCoordinates::Unit)));

    QObject::connect(&quit, SIGNAL( released() ),
                &a, SLOT( closeAllWindows() ) ) ;

    QObject::connect(&start, SIGNAL( released() ),
                &foo, SLOT( setStart() ) );

    QObject::connect(&destination, SIGNAL( released() ),
                &foo, SLOT( setEnd() ) );

    QObject::connect(&nav, SIGNAL( released() ),
            &foo, SLOT( setNav() ) );

    QObject::connect(&foo, SIGNAL( info_string(QString) ),
                &info, SLOT ( setText(QString) ) );

    w.setCentralWidget(&foo);
    w.show();

    return a.exec();
}
