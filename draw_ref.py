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
from pyqtgraph.Point import Point

import time as timelib
import re
import enum
#ENDPOINT = "ipc://routing.ipc"
ENDPOINT = "tcp://localhost:5555"
form_class = uic.loadUiType("drawwindow.ui")[0]
class SegmentEnum(enum.Enum):
    RAMP_UP = 0
    PLAT_TOP = 1
    RAMP_DOWN  = 2
    BREAK_DOWN = 3
    CONTROLLED_DOWN = 4
class PFEnum(enum.Enum):
    PF1 = 0
    PF2 = 1
    PF3U = 2
    PF3L = 3
    PF4U = 4
    PF4L = 5
    PF5U = 6
    PF5L = 7
    PF6U = 8
    PF6L = 9
    PF7 = 10
class DataTY():
    def __init__(self,tval,val):
        self.time = tval
        self.value = val
    def set_data(self, tval, val):
        if tval < -16 :
            print("DataTY: set_data tval is invalid : %d"%tval)
            return false
        self.time = tval
        self.value = val
    def get_data(self):
        return self.time, self.value
        
class PFCoils():
    def __init__(self):
        self.num_of_coil = 11
        self.sgmt_pts_list = []
        for i in range(11):
            self.sgmt_pts_list.append(SegmentPts())

    def set_data_pt(self, coil, segment,value):
        if (coil < 0) and (coil > self.num_of_coil) :
            return False
        self.sgmt_pts_list[coil].set_pt(segment,value)
        return True
    def set_data(self, coil, segment,tval, val):
        if (coil < 0) and (coil > self.num_of_coil) :
            return False
        value = DataTY(tval,val)
        self.sgmt_pts_list[coil].set_pt(segment,value)
        return True

    def get_data_pt(self,coil,segment,index):
        return self.sgmt_pts_list[coil].get_pt(segment,index)
    def get_data(self,coil,segment,index):
        data_ty= self.sgmt_pts_list[coil].get_pt(segment,index)
        return data_ty.get_data()
class SegmentPts():
    def __init__(self):
        self.num_of_segment = 5
        self.m_pts_rampup = []
        self.m_pts_plattop = []
        self.m_pts_rampdown = []
        self.m_pts_breakdown = []
        self.m_pts_controlleddown = []

        self.m_pts_rampup.append(Point(0,0))
        self.m_pts_plattop.append(Point(0,0))
        self.m_pts_rampdown.append(Point(0,0))
        self.m_pts_breakdown.append(Point(0,0))
        self.m_pts_controlleddown.append(Point(0,0))


    def get_len(self,segment):
        sgmt_len = -1
        if segment == SegmentEnum.RAMP_UP.value:
            sgmt_len = len(self.m_pts_rampup)
        elif segment == SegmentEnum.PLAT_TOP.value:
            sgmt_len = len(self.m_pts_plattop)
        elif segment == SegmentEnum.RAMP_DOWN.value:
            sgmt_len = len(self.m_pts_rampdown)
        elif segment == SegmentEnum.BREAK_DOWN.value:
            sgmt_len = len(self.m_pts_breakdown)
        elif segment == SegmentEnum.CONTROLLED_DOWN.value:
            sgmt_len = len(self.m_pts_controlleddown)
        return sgmt_len

    def set_pt(self, segment, value):
        if segment == SegmentEnum.RAMP_UP.value:
            self.m_pts_rampup.append(value)
        elif segment == SegmentEnum.PLAT_TOP.value:
            self.m_pts_plattop.append(value)
        elif segment == SegmentEnum.RAMP_DOWN.value:
            self.m_pts_rampdown.append(value)
        elif segment == SegmentEnum.BREAK_DOWN.value:
            self.m_pts_breakdown.append(value)
        elif segment == SegmentEnum.CONTROLLED_DOWN.value:
            self.m_pts_controlleddown.append(value)
        else:
            return False

    def get_pt(self,segment,index):
        if segment == SegmentEnum.RAMP_UP.value:
            if index < len(self.m_pts_rampup):
                return self.m_pts_rampup[index]
        elif segment == SegmentEnum.PLAT_TOP.value:
            if index < len(self.m_pts_plattop):
                return self.m_pts_plattop[index]
        elif segment == SegmentEnum.RAMP_DOWN.value:
            if index < len(self.m_pts_rampdown):
                return self.m_pts_rampdown[index]
        elif segment == SegmentEnum.BREAK_DOWN.value:
            if index < len(self.m_pts_breakdown):
                return self.m_pts_breakdown[index]
        elif segment == SegmentEnum.CONTROLLED_DOWN.value:
            if index < len(self.m_pts_controlleddown):
                return self.m_pts_controlleddown[index]
        else:
            return False

class WindowClass(QMainWindow, form_class) :
#class WindowClass(QMainWindow) :
    def __init__(self) :
        super().__init__()
#        uic.loadUi('button.ui',self)
        self.num_of_pf = 11
        self.num_of_sgmt = 5
        self.c_pts= []
        
        pg.setConfigOptions(antialias=True)
        self._counter = 0
        self.setupUi(self)
        self._log('[UI] started')
        self.txtBrw.ensureCursorVisible()
        self._log('[Thread] started')
        self.buff_size = 200
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        timestr = timelib.strftime("%Y%m%d-%H%M%S")
        print(timestr)
        self.m_gviews = []
        self.m_twidgets = []
        self.m_chks = []

        self.m_vbs = []
        self.m_pf_coils = PFCoils()

        for attr, value in self.__dict__.items():
            #m = re_p.match(attr)
            re_p_gv = re.compile('gview+')
            if(re_p_gv.match(attr)):
                print(attr, value)
                self.m_gviews.append(value)
            re_p_tw = re.compile('twidget+')
            if(re_p_tw.match(attr)):
                print(attr, value)
                self.m_twidgets.append(value)
            re_p_chk = re.compile('checkBox+')
            if(re_p_chk.match(attr)):
                print(attr, value)
                self.m_chks.append(value)

        for gv in self.m_gviews:
            gv.scene().sigMouseClicked.connect(self.mouse_clicked)
            self.m_vbs.append(gv.getViewBox())
            gv.setRange(xRange=[0,10], yRange=[0, 10])
        for tw in self.m_twidgets:
            tw.setRowCount(1)
            tw.setColumnCount(2)
            tw.setHorizontalHeaderLabels(["X","Y"])
            tw.setItem(0,0, QTableWidgetItem("0"))

        for chk in self.m_chks:
            chk.stateChanged.connect(self.checkBoxState)
        
        self.tabWidget.currentChanged.connect(self.onChange)
            # self.twidget.cellChanged.connect(self.cell_changed)
        print("tab position %d"% self.tabWidget.tabPosition())
        filename = "ref_%s.txt" %timestr
        # file save
        print(filename)
        self.refNameTextEdit.setPlainText(filename) 
        # button        
        self.updateButton.clicked.connect(self.updateButtonFunction)
        self.Save2FileButton.clicked.connect(self.Save2FileButtonFunction)
#         #버튼에 기능을 연결하는 코드
#         self.p = self.gview
#         self.p.addItem(self.vLine, ignoreBounds=True)
#         self.p.addItem(self.hLine, ignoreBounds=True)
#         print('widget size', self.p.geometry())
#         print('pixel size' , self.p.pixelSize())
#         self.p.scene().sigMouseClicked.connect(self.mouse_clicked)
#         #self.p.scene().sigMouseMoved.connect(self.mouseMoved)
#         #self.proxy = pg.SignalProxy(self.p.scene().sigMouseClicked, rateLimit=60, slot=self.mouse_clicked)
#         self.proxy = pg.SignalProxy(self.p.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
#         self.vb = self.p.getViewBox()
#         self.p.setRange(xRange=[0,100], yRange=[0, 100])
# #        self.p.enableAutoRange(axis='x')
# #        self.p2.enableAutoRange(axis='x')
        self.data = np.zeros(self.buff_size)

        self.time= np.zeros(self.buff_size)
        # self.c_pts.append(Point(0,0))
        # #self.data[:-1]=self.data[1:];self.data[-1] = float(0)
        # #self.time[:-1]=self.time[1:];self.time[-1] = 0
        # self.sizeArray = (np.random.random(500) * 20.).astype(int)
        self.ptr = 0
            
        # self.twidget.setRowCount(1)
        # self.twidget.setColumnCount(2)
        # self.twidget.setHorizontalHeaderLabels(["X","Y"])
        # self.twidget.setItem(0,0, QTableWidgetItem("0"))
        # self.twidget.cellChanged.connect(self.cell_changed)


        self.lastTime = time()

        self.nowTime = time()
        dt = self.nowTime-self.lastTime
        self.fps = -1.0#1.0/dt
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update)
#        self.timer.start(0)
        
        #sub_msg = self._sub.recv()
        #self._log(sub_msg)
    def checkBoxState(self):
        msg = ""
        chk_status  = []

        if self.m_chks[-1].isChecked() == True:
            for chk in self.m_chks:
                chk.setChecked(True)
            msg += "PF ALL is checked "
        else:
            for chk in self.m_chks:
                chk.setChecked(False)
            msg += "PF ALL is checked "

        for chk_idx in range(len(self.m_chks)):
            if self.m_chks[chk_idx].isChecked()== True:
                chk_status[chk_idx] = True
            else:
                chk_status[chk_idx] = False
        self.gview_ALL.clear()

        self._log(msg)
    def tabpos2idx(self,tab_pos,sub_tab_pos):
        return tab_pos*self.num_of_sgmt + sub_tab_pos
    def getTabPos(self):
        print("test getupfor1")
        print(PFEnum.PF3L)
        tab_pos = self.tabWidget.currentIndex()
        # try: myButton.clicked.disconnect() 
        # except Exception: pass
        sub_tab_pos = -1
        print("tab position %d"% tab_pos)
        if tab_pos == PFEnum.PF1.value:
            sub_tab_pos = self.subTabWidget_1.currentIndex()
            
        elif tab_pos == PFEnum.PF2.value:
            sub_tab_pos = self.subTabWidget_2.currentIndex()
        elif tab_pos == PFEnum.PF3U.value:
            sub_tab_pos = self.subTabWidget_3u.currentIndex()
        elif tab_pos == PFEnum.PF3L.value:
            print("debugdebug")
            sub_tab_pos = self.subTabWidget_3l.currentIndex()
            print("debug :tab pos  = %d, sub tab pos = %d\n"%( tab_pos, sub_tab_pos))
        elif tab_pos == PFEnum.PF4U.value:
            sub_tab_pos = self.subTabWidget_4u.currentIndex()
        elif tab_pos == PFEnum.PF4L.value:
            sub_tab_pos = self.subTabWidget_4l.currentIndex()
        elif tab_pos == PFEnum.PF5U.value:
            sub_tab_pos = self.subTabWidget_5u.currentIndex()
        elif tab_pos == PFEnum.PF5L.value:
            sub_tab_pos = self.subTabWidget_5l.currentIndex()
        elif tab_pos == PFEnum.PF6U.value:
            sub_tab_pos = self.subTabWidget_6u.currentIndex()
        elif tab_pos == PFEnum.PF6L.value:
            sub_tab_pos = self.subTabWidget_6l.currentIndex()
        elif tab_pos == PFEnum.PF7.value:
            sub_tab_pos = self.subTabWidget_7.currentIndex()
        else:
            sub_tab_pos = -1
        print("tab pos  = %d, sub tab pos = %d\n"%( tab_pos, sub_tab_pos))
        return tab_pos, sub_tab_pos
        
    def onChange(self):
        tab_pos, sub_tab_pos = self.getTabPos()
        # try: myButton.clicked.disconnect() 
        # except Exception: pass

        
        #print("subtab position %d"% self.subTabWidget_2.currentIndex())
        

    def updateButtonFunction(self):
        timestr = timelib.strftime("%Y%m%d-%H%M%S")
        print(timestr)

        filename = "ref_%s.txt" %timestr
        print(filename)
        self.refNameTextEdit.setPlainText(filename)
        self._update()
    def Save2FileButtonFunction(self):
        filename=self.refNameTextEdit.toPlainText()
        self.f = open(filename,"w")
        for i in range(len(self.c_pts)):
            data = self.c_pts[i].y()
            time = self.c_pts[i].x()
            wdata = "%f,%f\n" %(data,time)
            print(wdata)
            self.f.write(wdata)
        print("Write2File is Done!!\n")
        self.f.close()
    @pyqtSlot()
    def cell_changed(self):
        print('cell changed')
        try:
            self.cell = self.twidget.currentItem()
            print('[cell ch] cell ch',self.cell.text())
            self.col = self.twidget.currentItem().column()
            self.row = self.twidget.currentItem().row()
            print('[cell ch] row,col',self.row,self.col)
            p_var = self.c_pts[self.row] #(x,y)
            #self.c_pts[self.row] = Point(0,0)  # x = (i,0), y = (i,1)
            print(p_var.x())
            print(self.row, self.c_pts[self.row])
            if self.col is 0:
                print('self.col is 0')
                print(self.cell.text())
                self.c_pts[self.row] = Point(int(self.cell.text()),p_var.y())
            else:
                print('self.col is 1')
                self.c_pts[self.row] = Point(p_var.x(),int(self.cell.text()))
            print('x = %d' %(self.c_pts[self.row].x()))
            print('y= %d'%(self.c_pts[self.row].y()))
        except:
            pass
    def mouseMoved(self,evt):
        #print(evt)
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
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
#            self.p.clear()
#            self._update()
    def mouse_clicked(self,evt):
        print("test")
        print(evt)
       
        # m_pt = self.vb.mapSceneToView(evt.scenePos())
        tab_pos, sub_tab_pos = self.getTabPos()
        coil_idx = tab_pos
        sgmt_idx = sub_tab_pos
        print("tab pos  = %d, sub tab pos = %d\n", tab_pos, sub_tab_pos)
        t_idx = self.tabpos2idx(tab_pos,sub_tab_pos)
        m_pt = self.m_vbs[t_idx].mapSceneToView(evt.scenePos())
        self.m_pf_coils.set_data_pt(coil_idx,sgmt_idx,m_pt)
        #pos = evt[0]#pos = evt.pos()
        #m_pt = self.vb.mapSceneToView(evt.pos())
       
        print('m_pt', m_pt)
        print('m_pt.x', m_pt.x())
        self.c_pts.append(m_pt)
        
        self._update()


    def mouseReleaseEvent(self, e):
        self.c_pts.append(e.pos())
        print('button release')
        
        msg = 'pos' + str(e.x()) +', ' +str(e.y()) 
        self._log(msg)
        # self.chosen_points.append(self.mapFromGlobal(QtGui.QCursor.pos()))
        self.update()
    def _update(self):
        tab_pos, sub_tab_pos = self.getTabPos()
        t_idx = self.tabpos2idx(tab_pos,sub_tab_pos)
        self.m_gviews[t_idx].clear()
        t_pts_size = self.m_pf_coils.sgmt_pts_list[tab_pos].get_len(sub_tab_pos)
        for i in range(t_pts_size):
            t_pt = self.m_pf_coils.get_data_pt(tab_pos,sub_tab_pos,i)
            self.data[i] = t_pt.y()
            self.time[i] = t_pt.x()
            print("[%d]:%d "%(i, self.data[i]))
            row_count =  self.m_twidgets[t_idx].rowCount()
            if row_count < t_pts_size:
                self.m_twidgets[t_idx].setRowCount(row_count+1)
            
            x_item = QTableWidgetItem(str(t_pt.x()))
            y_item = QTableWidgetItem(str(t_pt.y()))
            x_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            y_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.m_twidgets[t_idx].setItem(i,0,x_item)
            self.m_twidgets[t_idx].setItem(i,1,y_item)
        curve = pg.PlotCurveItem(x=self.time, y=self.data,
                            pen='g', brush='b',size = t_pts_size)
        for i in range(t_pts_size) :
            scatter = pg.ScatterPlotItem(x=[self.time[i]], y=[self.data[i]], size = 10, pen='r', brush='b')
            self.m_gviews[t_idx].addItem(scatter)
        curve.setClickable(True)
        self.m_gviews[t_idx].showGrid(x = True, y = True, alpha = 1.0)
        self.m_gviews[t_idx].addItem(curve)
        self.ptr += 1
        now = time()
        dt = now - self.lastTime
        self.lastTime = time()
        if self.fps < 0:
            self.fps = 1.0/dt
        else:
            s = np.clip(dt*3.,0,1)
            self.fps = self.fps*(1-s) + (1.0/dt)*s
        self.m_gviews[t_idx].setTitle('%0.2f fps' % self.fps)
        self.m_gviews[t_idx].repaint()

        # self.p.clear()
        # #if self.ptr > self.buff_size: 
        # #   self.p.enableAutoRange(axis='x')
        # #self.p.enableAutoRange(axis='x')
        # #self.p.enableAutoRange(axis='x')
        # self.size = self.sizeArray
        # c_pts_size = len(self.c_pts)
        # for i in range(len(self.c_pts)):
        #     self.data[i] = self.c_pts[i].y()
        #     self.time[i] = self.c_pts[i].x()
        #     print("[%d]:%d "%(i, self.data[i]))
        #     row_count =  self.twidget.rowCount()
        #     if row_count < c_pts_size:
        #         self.twidget.setRowCount(row_count+1)

        #     x_item = QTableWidgetItem(str(self.c_pts[i].x()))
        #     y_item = QTableWidgetItem(str(self.c_pts[i].y()))
        #     x_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        #     y_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        #     self.twidget.setItem(i,0,x_item)
        #     self.twidget.setItem(i,1,y_item)
        # #self.data[:-1]=self.data[1:];self.data[-1] = float(rtval)
        # #self.time[:-1]=self.time[1:];self.time[-1] = self.ptr
        # curve = pg.PlotCurveItem(x=self.time, y=self.data,
        #                             pen='g', brush='b',size = self.size)
        # self.size = len(self.c_pts)
        # for i in range(self.size) :
        #     scatter = pg.ScatterPlotItem(x=[self.time[i]], y=[self.data[i]], size = 10, pen='r', brush='b')
        #     self.p.addItem(scatter)
        # curve.setClickable(True)
        # self.p.showGrid(x = True, y = True, alpha = 1.0)
        # self.p.addItem(curve)
        # self.ptr += 1
        # now = time()
        # dt = now - self.lastTime
        # self.lastTime = time()
        # if self.fps < 0:
        #     self.fps = 1.0/dt
        # else:
        #     s = np.clip(dt*3.,0,1)
        #     self.fps = self.fps*(1-s) + (1.0/dt)*s
        # self.p.setTitle('%0.2f fps' % self.fps)
        # self.p.repaint()

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
    
