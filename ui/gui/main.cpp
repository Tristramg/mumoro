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


MyMarble::MyMarble(const char * db, QWidget * w) :
    MarbleWidget(w), p(db, Mumoro::Foot), start_defined(false), end_defined(false) {}

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
        painter->setPen( QColor( 255, 0, 0 ) );
        std::list<std::pair<double,double> >::const_iterator i = path.begin();
        GeoDataLineString l;
        for(i = path.begin(); i != path.end(); i++)
        {
            l.append( new GeoDataCoordinates( (*i).first, (*i).second, 0,
                        GeoDataCoordinates::Degree));

        }
        painter->drawPolyline(l);
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
            path = p.compute_lon_lat(start.id, end.id);
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

    MyMarble foo( argv[1] );
    foo.setMapThemeId( "earth/openstreetmap/openstreetmap.dgml" );
    foo.setShowOverviewMap( false );
    foo.setShowCompass( false );

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
