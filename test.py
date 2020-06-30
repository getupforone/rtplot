import sys
import numpy
from PyQt5 import QtCore, QtGui,uic,QtWidgets
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import os


hw,QtBaseClass=uic.loadUiType("test.ui")
def gaussian(A, B, x):
    return A * numpy.exp(-(x / (2. * B)) ** 2.)
class MyApp(QtWidgets.QMainWindow, hw):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        winSize=self.size()
        self.view.resize(winSize.width(),winSize.height())
        x = numpy.linspace(-5., 5., 10000)
        y =gaussian(5.,0.2, x)
        self.p=self.view.plot(x,y)

        proxy = pg.SignalProxy(self.view.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.view.enableAutoRange("xy", True)

 



        Plotted = self.plot
        vLine = pg.InfiniteLine(angle=90, movable=False)
        hLine = pg.InfiniteLine(angle=0, movable=False)
        Plotted.addItem(vLine, ignoreBounds=True)
        Plotted.addItem(hLine, ignoreBounds=True)
        Plotted.setMouseTracking(True)
        Plotted.scene().sigMouseMoved.connect(self.mouseMoved)

        def mouseMoved(self,evt):
                pos = evt
                if self.plot.sceneBoundingRect().contains(pos):
                    mousePoint = self.plot.plotItem.vb.mapSceneToView(pos)
                    self.label.setText("<span style='font-size: 15pt'>X=%0.1f, <span style='color: black'>Y=%0.1f</span>" % (mousePoint.x(),mousePoint.y()))
                self.plot.plotItem.vLine.setPos(mousePoint.x())
                self.plot.plotItem.hLine.setPos(mousePoint.y()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()

    sys.exit(app.exec_())