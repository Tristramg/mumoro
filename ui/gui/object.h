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

#include <QtGui/QApplication>
#include <QtCore/QDebug>
#include "marble/MarbleWidget.h"
#include "../../lib/shortest_path.h"
using namespace Marble;

class MyMarble : public MarbleWidget
{
    Mumoro::Node start, end; 
    Mumoro::Shortest_path p;
    std::list<std::pair<double,double> > path;
    int click_action;
    enum {NAV, SEL_START, SEL_DEST};
    bool start_defined;
    bool end_defined;
    bool path_calculated;
    Q_OBJECT
    public:
        QString gen_info();
        MyMarble( const char*, QWidget * w = 0 );
        void customPaint( GeoPainter *painter );
    public slots:
    void mouseClickGeoPosition(qreal,qreal,GeoDataCoordinates::Unit);
    void setNav();
    void setStart();
    void setEnd();
    signals:
        void info_string(QString);
};

