import sys
from threading import Thread
from pyqtgraph import PlotWidget
from pyqtgraph.Qt import QtGui, QtCore, QT_LIB
import pyqtgraph as pg
from PyQt5.QtCore import QPoint,pyqtSlot, pyqtSignal, QObject, Qt, QThread, QTimer
#from pyqtgraph import PlotWidget
import signal
import uuid
import zmq
from PyQt5.QtWidgets import *
#from PyQt5.QtCore import *
from PyQt5.QtCore import QSocketNotifier
from PyQt5 import uic
import numpy as np
from pyqtgraph.ptime import time


#ENDPOINT = "ipc://routing.ipc"
ENDPOINT = "tcp://localhost:5555"
form_class = uic.loadUiType("drawwindow.ui")[0]


class WindowClass(QMainWindow, form_class) :
#class WindowClass(QMainWindow) :
    def __init__(self) :
        super().__init__()
#        uic.loadUi('button.ui',self)
        self.c_pts= []
        pg.setConfigOptions(antialias=True)
        self._counter = 0
        self.setupUi(self)
        self._log('[UI] started')
        self.txtBrw.ensureCursorVisible()
        self._log('[Thread] started')
        self.buff_size = 200
        #버튼에 기능을 연결하는 코드
        self.p = self.gview
        print('widget size', self.p.geometry())
        print('pixel size' , self.p.pixelSize())
        self.p.scene().sigMouseClicked.connect(self.mouse_clicked)
        #self.p.scene().sigMouseMoved.connect(self.mouseMoved)
        #self.proxy = pg.SignalProxy(self.p.scene().sigMouseClicked, rateLimit=60, slot=self.mouse_clicked)
        self.proxy = pg.SignalProxy(self.p.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.vb = self.p.getViewBox()
        self.p.setRange(xRange=[0,100], yRange=[0, 100])
#        self.p.enableAutoRange(axis='x')
#        self.p2.enableAutoRange(axis='x')
        self.data = np.zeros(self.buff_size)

        self.time= np.zeros(self.buff_size)
        #self.data[:-1]=self.data[1:];self.data[-1] = float(0)
        #self.time[:-1]=self.time[1:];self.time[-1] = 0
        self.sizeArray = (np.random.random(500) * 20.).astype(int)
        self.ptr = 0
            
        self.lastTime = time()

        self.nowTime = time()
        dt = self.nowTime-self.lastTime
        self.fps = -1.0#1.0/dt
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(0)
        
        #sub_msg = self._sub.recv()
        #self._log(sub_msg)
    def mouseMoved(self,evt):
        print(evt)
#        pos = evt.scenePos()
#        if self.p.sceneBoundingRect().contains(pos):
#            mousePoint = self.vb.mapSceneToView(pos)
#            index = int(mousePoint.x())
#            if index > 0 :
#                self.coorlabel.setText("<span style='font-size: 12pt'>x=%0.1f</span>" % (mousePoint.x()))
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.p.sceneBoundingRect().contains(pos):
            mousePoint = self.vb.mapSceneToView(pos)
            index = int(mousePoint.x())
            if index > 0 :
                self.coorlabel.setText("<span style='font-size: 12pt'><span style='color: green'>x=%0.1f y=%0.1f</span>" % (mousePoint.x(),mousePoint.y()))
    def mouse_clicked(self,evt):
        print("test")
        print(evt)
        #pos = evt[0]#pos = evt.pos()
        #m_pt = self.vb.mapSceneToView(evt.pos())
        m_pt = self.vb.mapSceneToView(evt.scenePos())
        print('m_pt', m_pt)
        self.c_pts.append(m_pt)
#        # mouseClickEvent is a pyqtgraph.GraphicsScene.mouseEvents.MouseClickEvent
#        print('clicked plot 0x{:x}, event: {}'.format(id(self), mouseClickEvent))
#        print('pixel size' , self.p.pixelSize())
#        print('view rect' , self.p.viewRect())
#        #if(mouseClickEvent.pos() != NoneType):
#        print('view box' ,self.p.mapSceneToView(mouseClickEvent.pos()))
#        #items = self.p.scene().items(mouseClickEvent.scenePos())
#        #print ("Plots:", [x for x in items if isinstance(x, pg.PlotItem)])
#        #self.p.scene()currentItem.mapFromScene(self._lastScenePos
#        if( mouseClickEvent.currentItem is not  None):
#            #p = mouseClickEvent.pos()
#            scene_pos = mouseClickEvent.scenePos()
#            screen_pos = mouseClickEvent.screenPos()
#            #cc_pos = mouseClickEvent.currentItem.mapFromScene(scene_pos) 
#            #
#            print('geometry = :', self.p.geometry())
#            c_pos_x = scene_pos.x() + self.p.geometry().x()
#            c_pos_y = self.p.geometry().height() - scene_pos.y() + self.p.geometry().y()
#            qpt = QPoint(c_pos_x, c_pos_y)
#            print(scene_pos.x(), c_pos_y)
#            p = mouseClickEvent.pos()
#            self.c_pts.append(qpt)
#            print('test',self.p.mapToScene(scene_pos))
#            msg = 'pos' + str(p.x()) +', ' +str(p.y())
#            scene_msg = '[scene pos]' + str(scene_pos.x()) +', ' +str(scene_pos.y())
#            screen_msg = '[screen pos]' + str(screen_pos.x()) +', ' +str(screen_pos.y())
#            screen_msg = '[screen pos]' + str(screen_pos.x()) +', ' +str(screen_pos.y())
#            qpt_msg = '[qpt pos]' + str(qpt.x()) +', ' +str(qpt.y())
#            self._log(screen_msg)
#            self._log(scene_msg)
#            self._log(qpt_msg)
#        else:
#            msg = 'none pose'
#        self._log(msg)

    def mouseReleaseEvent(self, e):
        self.c_pts.append(e.pos())
        print('button release')
        
        msg = 'pos' + str(e.x()) +', ' +str(e.y()) 
        self._log(msg)
        # self.chosen_points.append(self.mapFromGlobal(QtGui.QCursor.pos()))
        self.update()
    def _update(self):
        
        self.p.clear()
        #if self.ptr > self.buff_size: 
        #   self.p.enableAutoRange(axis='x')
        #self.p.enableAutoRange(axis='x')
        #self.p.enableAutoRange(axis='x')
        self.size = self.sizeArray
        rtval = np.random.randint(0,100)
        for i in range(len(self.c_pts)):
            self.data[i] = self.c_pts[i].y()
            self.time[i] = self.c_pts[i].x()

        #self.data[:-1]=self.data[1:];self.data[-1] = float(rtval)
        #self.time[:-1]=self.time[1:];self.time[-1] = self.ptr
        curve = pg.PlotCurveItem(x=self.time, y=self.data,
                                    pen='g', brush='b',size = self.size)
        self.size = len(self.c_pts)
        for i in range(self.size) :
            scatter = pg.ScatterPlotItem(x=[self.time[i]], y=[self.data[i]], size = 10, pen='r', brush='b')
            self.p.addItem(scatter)
        curve.setClickable(True)
        self.p.showGrid(x = True, y = True, alpha = 1.0)
        self.p.addItem(curve)
        self.ptr += 1
        now = time()
        dt = now - self.lastTime
        self.lastTime = time()
        if self.fps < 0:
            self.fps = 1.0/dt
        else:
            s = np.clip(dt*3.,0,1)
            self.fps = self.fps*(1-s) + (1.0/dt)*s
        self.p.setTitle('%0.2f fps' % self.fps)
        self.p.repaint()

    def _log(self, data):
        text = self.txtBrw.toPlainText()
        self.txtBrw.setPlainText(text + data + '\n')
        self.txtBrw.moveCursor(QtGui.QTextCursor.End)



if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass() 
    myWindow.show()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.exec_()
    