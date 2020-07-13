import sys
from threading import Thread
from pyqtgraph import PlotWidget
from pyqtgraph.Qt import QtGui, QtCore, QT_LIB
import pyqtgraph as pg
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, Qt, QThread, QTimer
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
import h5py


#ENDPOINT = "ipc://routing.ipc"
ENDPOINT = "tcp://localhost:5555"
form_class = uic.loadUiType("mainwindow.ui")[0]
class Subscriber():
    def __init__(self):
        context = zmq.Context.instance()
        sub = context.socket(zmq.SUB)
        sub.setsockopt(zmq.SUBSCRIBE, b'topic1')
        #sub.setsockopt(zmq.SUBSCRIBE, b"")
        #sub.setsockopt_string(zmq.SUBSCRIBE, '')
        sub.connect("tcp://localhost:7777")
        self.socket = sub

    def recv(self):
        return self.socket.recv_multipart()

class Client():
    def __init__(self):
        context = zmq.Context.instance()
        client = context.socket(zmq.DEALER)
        client.setsockopt(zmq.IDENTITY, b'QtClient')
        client.connect(ENDPOINT)

        self.socket = client

    def dispatch(self, msg):
        msg = bytes(msg, 'utf-8')
        uid = uuid.uuid4().bytes
        self.socket.send_multipart([uid, msg])
        return uid

    def recv(self):
        print("msg recved")
        return self.socket.recv_multipart()

class WindowClass(QMainWindow, form_class) :
#class WindowClass(QMainWindow) :
    def __init__(self) :
        super().__init__()
#        uic.loadUi('button.ui',self)

        pg.setConfigOptions(antialias=True)
        self._client = Client()
        socket = self._client.socket
        self._notifier = QSocketNotifier(socket.getsockopt(zmq.FD),QSocketNotifier.Read,self)
        self._notifier.activated.connect(self._socket_activity)
        self._counter = 0
        self.setupUi(self)
        self._log('[UI] started')

        s_thrd = Thread(target=self.sub_thrd)
        s_thrd.start()
        self._log('[Thread] started')
        self.buff_size = 200
        #버튼에 기능을 연결하는 코드
        self.pBut.clicked.connect(self.button1Function)
        self.p = self.gview

        self.p.setRange(xRange=[0, self.buff_size], yRange=[0, 500])
        self.p2 = self.gview_2
        self.p2.setRange(xRange=[0, self.buff_size], yRange=[-250, 250])
#        self.p.enableAutoRange(axis='x')
#        self.p2.enableAutoRange(axis='x')
        self.data = np.empty(self.buff_size)
        self.data2 = np.empty(self.buff_size)
        self.time = np.empty(self.buff_size)
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
    def sub_thrd(self):
        _sub = Subscriber()
        print("thrd sub start")
        while True:
            msg = dict(zip('topic1', (x.decode() for x in _sub.recv())))
            #id, msg = _sub.recv();
            #msg = _sub.recv();
            #print("[sub_thrd][%s] : %s" %(id, msg))
            #print("[sub_thrd] : %s" %( msg))
            for k,v in msg.items():
                print(f'{k}: {v}')
            #self._log(msg)
    def _update(self):
        
        self.p.clear()
        self.p2.clear()
        if self.ptr > self.buff_size: 
           self.p.enableAutoRange(axis='x')
           self.p2.enableAutoRange(axis='x')
        if self.randCheck.isChecked():
            self.size = self.sizeArray
        else:
            self.size = self.sizeSpin.value()
        rtval = np.random.randint(0,100)
        self.data[:-1]=self.data[1:];self.data[-1] = float(rtval)
        self.data2 = self.data+50
        self.time[:-1]=self.time[1:];self.time[-1] = self.ptr
        curve = pg.PlotCurveItem(x=self.time, y=self.data,
                                    pen='g', brush='b',size = self.size)
        curve2 = pg.PlotCurveItem(x=self.time, y=self.data2,
                                    pen='r', brush='b',size = self.size)
        self.p.addItem(curve)
        self.p2.addItem(curve2)
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

    def _send_data(self):
        msg = "Test message #" + str(self._counter)
        self._client.dispatch(msg)
        self._log("[UI] sent: " + msg)
        self._counter += 1

    def _socket_activity(self):
        self._notifier.setEnabled(False)

        flags = self._client.socket.getsockopt(zmq.EVENTS)
        self._log("[Socket] socket.getsockopt(zmq.EVENTS): " + repr(flags))

        if flags & zmq.POLLIN:
            received = self._client.recv()
            self._log("[Socket] zmq.POLLIN")
            self._log("[Socket] received: " + repr(received))
        elif flags & zmq.POLLOUT:
            self._log("[Socket] zmq.POLLOUT")
        elif flags & zmq.POLLERR:
            self._log("[Socket] FAILURE")

        self._notifier.setEnabled(True)

        flags = self._client.socket.getsockopt(zmq.EVENTS)
        self._log("[Socket] socket.getsockopt(zmq.EVENTS): " + repr(flags))

    def button1Function(self) :
        print("btn_1 Clicked")
        self.txtBrw.append("pBut clicked")
        self._send_data()



if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass() 
    myWindow.show()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.exec_()
    
