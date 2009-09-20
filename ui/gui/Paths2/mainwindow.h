#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include "MultimodalGraph.h"
#include "martins.h"

#include <QtGui/QMainWindow>
#include "qmapcontrol/qmapcontrol.h"

namespace Ui {
    class MainWindow;
}
using namespace qmapcontrol;
class MainWindow : public QMainWindow {
    Q_OBJECT
public:
    MainWindow(QWidget *parent = 0);
    ~MainWindow();
    void compute();

protected:
    void resizeEvent(QResizeEvent * e);
    void keyPressEvent(QKeyEvent* evnt);
private:
    MultimodalGraph g;
    Ui::MainWindow *m_ui;
    QAction * startAct;
    QAction * destAct;
    QAction * centerAct;
    QPointF lastClick;
    ImagePoint * start;
    ImagePoint * stop;
    Layer* l;
    GeometryLayer * ll;
    std::vector<LineString *> path;
    node_t start_node;
    node_t dest_node;
    std::vector<Path> paths;

public slots:
    void geometryClicked(Geometry* geom, QPoint coord_px);
    void mouseEventCoordinate ( const QMouseEvent* evnt, const QPointF coordinate );
    void setStart();
    void setDestination();
    void displayPath(size_t nb);
    void cellClicked(int, int);


};

#endif // MAINWINDOW_H
