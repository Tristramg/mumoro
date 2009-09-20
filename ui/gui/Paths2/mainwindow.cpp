#include "mainwindow.h"
#include "ui_mainwindow.h"
#include "MultimodalGraph.h"
using namespace std;

MainWindow::~MainWindow()
{
    delete m_ui;
}


MainWindow::MainWindow(QWidget *parent)
        : QMainWindow(parent), m_ui(new Ui::MainWindow)
{
    std::string path = ".";
    std::pair<int, int> a, b, c, d;
    a = g.load("bike", path + "/nodes.csv", path+"/edges.csv", Bike);
    cout << "Loaded " << a.first << " nodes, and " << a.second << " edges" << endl;

/*    b = g.load("bart", path + "/stops_bart.txt", path+"/stop_times_bart.txt", PublicTransport);
    cout << "Loaded " << b.first << " nodes, and " << b.second << " edges" << endl;

    c = g.load("muni", path + "/stops_muni.txt", path+"/stop_times_muni.txt", PublicTransport);
    cout << "Loaded " << c.first << " nodes, and " << c.second << " edges" << endl;

    d = g.load("bike", path + "/nodes_l.csv", path+"/edges_l.csv", Bike);
    cout << "Loaded " << d.first << " nodes, and " << d.second << " edges" << endl;

    Edge interconnexion;
    interconnexion.distance = 0;
    interconnexion.duration = Duration(30);
    interconnexion.elevation = 0;
    interconnexion.nb_changes = 1;
    cout << "Nb of interconnecting edges: " << g.connect_closest("bart", "foot", interconnexion) << endl;
    cout << "Nb of interconnecting edges: " << g.connect_closest("muni", "foot", interconnexion) << endl;
    cout << "Nb of interconnecting edges: " << g.connect_same_nodes("bike", "foot", interconnexion, false) << endl;

*/
    m_ui->setupUi(this);


    // create layer
    MapAdapter* mapadapter = new OSMMapAdapter();
    l = new MapLayer("Custom Layer", mapadapter);
    ll = new GeometryLayer("Geometry", mapadapter,true);
    m_ui->mc->addLayer(l);
    m_ui->mc->addLayer(ll);

    this->start = NULL;
    this->stop = NULL;


    // Connect click events of the layer to this object
    connect(l, SIGNAL(geometryClicked(Geometry*, QPoint)),
            this, SLOT(geometryClicked(Geometry*, QPoint)));
    connect(m_ui->mc, SIGNAL(mouseEventCoordinate(const QMouseEvent*,QPointF)),
            this, SLOT(mouseEventCoordinate(const QMouseEvent*,QPointF)));

    m_ui->mc->enablePersistentCache();
    m_ui->mc->mouseMode();
    startAct = new QAction(tr("Set start"), this);
    connect(startAct, SIGNAL(triggered()), this, SLOT(setStart()));

    destAct = new QAction(tr("Set destination"), this);
    connect(destAct, SIGNAL(triggered()), this, SLOT(setDestination()));

    this->m_ui->PathInfoDock->close();

}


void MainWindow::geometryClicked(Geometry* geom, QPoint)
{
    qDebug() << "parent: " << geom->parentGeometry();
    qDebug() << "Element clicked: " << geom->name();
    if (geom->hasClickedPoints())
    {
        QList<Geometry*> pp = geom->clickedPoints();
        qDebug() << "number of child elements: " << pp.size();
        for (int i=0; i<pp.size(); i++)
        {
            QMessageBox::information(this, geom->name(), pp.at(i)->name());
        }
    }
    else if (geom->GeometryType == "Point")
    {
        QMessageBox::information(this, geom->name(), "just a point");
    }
}
void MainWindow::mouseEventCoordinate ( const QMouseEvent* evnt, const QPointF coordinate )
{
    if (evnt->type() == QMouseEvent::MouseButtonRelease && evnt->button() == 2)
    {
        this->lastClick = coordinate;
        QMenu menu(this);
        menu.addAction(startAct);
        menu.addAction(destAct);
        menu.exec(evnt->globalPos());

    }

}

void MainWindow::keyPressEvent(QKeyEvent* evnt)
{
    if (evnt->key() == 49 || evnt->key() == 17825792)  // tastatur '1'
    {
        m_ui->mc->zoomIn();
    }
    else if (evnt->key() == 50)
    {
        m_ui->mc->moveTo(QPointF(8.25, 60));
    }
    else if (evnt->key() == 51 || evnt->key() == 16777313)     // tastatur '3'
    {
        m_ui->mc->zoomOut();
    }
    else if (evnt->key() == 54) // 6
    {
        m_ui->mc->setView(QPointF(8,50));
    }
    else if (evnt->key() == 16777234) // left
    {
        m_ui->mc->scrollLeft();
    }
    else if (evnt->key() == 16777236) // right
    {
        m_ui->mc->scrollRight();
    }
    else if (evnt->key() == 16777235 ) // up
    {
        m_ui->mc->scrollUp();
    }
    else if (evnt->key() == 16777237) // down
    {
        m_ui->mc->scrollDown();
    }
    else if (evnt->key() == 48 || evnt->key() == 17825797) // 0
    {
        emit(close());
    }
    else
    {
        qDebug() << evnt->key() << endl;
    }
}

void MainWindow::resizeEvent(QResizeEvent * e)
{
    m_ui->mc->resize(e->size());
}

void MainWindow::setStart()
{
    try{
        node_t matched = g["bike"].match(this->lastClick.x(), this->lastClick.y());
        float lon = g[matched].lon;
        float lat = g[matched].lat;
        m_ui->start_label->setText(QString("Lon: %1, lat %2 = %3").arg(this->lastClick.x()).arg(this->lastClick.y()).arg(g[matched].id.c_str()));
        if(start != NULL)
            this->ll->removeGeometry(start);
        start = new ImagePoint(lon, lat, ":/images/arrow-green.png", "Start", Point::BottomRight);
        this->ll->addGeometry(start);
        start_node = matched;
        this->compute();
    }
    catch(match_failed)
    {
        if(start != NULL)
            this->ll->removeGeometry(start);
        m_ui->start_label->setText("Match failed");
    }
}



void MainWindow::setDestination()
{
    try
    {
        node_t matched = g["bike"].match(this->lastClick.x(), this->lastClick.y());
        float lon = g[matched].lon;
        float lat = g[matched].lat;
        m_ui->dest_label->setText(QString("Lon: %1, lat %2 = %3").arg(this->lastClick.x()).arg(this->lastClick.y()).arg(g[matched].id.c_str()));
        if(stop != NULL)
            this->ll->removeGeometry(stop);
        stop = new ImagePoint(lon, lat, ":/images/arrow-finish.png", "Destination", Point::BottomRight);
        this->ll->addGeometry(stop);
        dest_node = matched;
        this->compute();
    }
    catch(match_failed)
    {
        if(stop != NULL)
            this->ll->removeGeometry(stop);
        m_ui->dest_label->setText("Match failed");
    }
}

void MainWindow::compute()
{
    if(stop != NULL && stop != NULL)
    {
        cout << "Starting the martins algorithm. Let's see what happens" << endl;
        vector<Path> labels = martins(start_node, dest_node, g, &Edge::elevation);
        this->m_ui->result_label->setText(QString("Nb solutions = %1").arg(labels.size()));
        int i = 0;
        this->m_ui->result_table->setRowCount(labels.size());
        for(vector<Path>::iterator it = labels.begin(); it != labels.end(); it++)
        {
            QTableWidgetItem *  foo;
            foo = new QTableWidgetItem(QString("%1").arg(it->cost[0]));
            this->m_ui->result_table->setItem(i, 0, foo);
            foo = new QTableWidgetItem(QString("%1").arg(it->cost[1]));
            this->m_ui->result_table->setItem(i, 1, foo);
            foo = new QTableWidgetItem(QString("%1").arg(it->cost[2]));
            this->m_ui->result_table->setItem(i, 2, foo);
      //      foo = new QTableWidgetItem(QString("%1").arg(it->size()));
      //      this->m_ui->result_table->setItem(i, 3, foo);
            i++;
        }
        cout << "Nb of labels: " << labels.size();
        paths = labels;
    }

}

void MainWindow::displayPath(size_t nb)
{
    for(size_t i=0; i < path.size(); i++)
    {
        this->ll->removeGeometry(path[i]);
    }
    path.clear();

    list<Node>::const_iterator it;
    this->m_ui->path_info->clear();
    QString s;
    std::string last_layer;
    LineString * temp = NULL;

    for(it = paths[nb].nodes.begin(); it != paths[nb].nodes.end(); it++)
    {
        if( last_layer != it->layer )
        {
            if(temp != NULL)
            {
                path.push_back(temp);
                ll->addGeometry(temp);
                last_layer = it->layer;
            }
            temp = new LineString();
            if(it->layer == "foot")
                temp->setPen(new QPen(Qt::green, 3));
            else if(it->layer == "bart")
                temp->setPen(new QPen(Qt::blue, 3));
            else if(it->layer == "muni")
                temp->setPen(new QPen(Qt::red, 3));
            else
                temp->setPen(new QPen(Qt::yellow, 3));
        }
        temp->addPoint(new Point(it->lon, it->lat));
        s.append(QString("%1 <br>").arg(it->id.c_str()));
    }
    path.push_back(temp);
    ll->addGeometry(temp);
    this->m_ui->path_info->setText(s);
}

void MainWindow::cellClicked(int row, int)
{
    displayPath(row);
}
