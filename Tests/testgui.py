from PyQt5.QtWidgets import *
from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSlot
import asyncio
import sys
sys.path.append('../')
from qweather import QWeatherClient


class testgui(QWidget):

    def __init__(self,loop):
        super().__init__()

        self.setWindowTitle('Test GUI')

        self.initialize()
        brokerconn = "tcp://localhost:5559"
        self.client = QWeatherClient(brokerconn,loop = loop,name='testgui')
        self.client.subscribe('TestServer',self.print_message)
        self.loop = loop
        self.loop.create_task(self.client.run())

    def initialize(self):
        sendbutton = QPushButton('Send command to server 1')
        l1 = QLabel()
        l2 = QLabel()
        sendbutton2 = QPushButton('Send command to server 2')
        layout = QVBoxLayout()
        layout.addWidget(sendbutton)
        layout.addWidget(l1)
        layout.addWidget(sendbutton2)
        layout.addWidget(l2)

        sendbutton.pressed.connect(lambda : self.loop.create_task(self.send_command(self.client.TestServer.do_something_scheduled())))
        sendbutton2.pressed.connect(lambda : self.loop.create_task(self.send_command(self.client.TestServer2.get_number(),l2)))
        self.setLayout(layout)
        self.show()

    def print_message(self,msg):
        print('msg> ', msg)

    async def send_command(self,func):
        a = await func
        
    def closeEvent(self,e):
        self.loop.stop()


async def process_events(qapp):
    while True:
        await asyncio.sleep(0.1)
        qapp.processEvents()



if __name__=="__main__":
    a = QApplication( [] )
#    loop = QEventLoop(a)
 #   asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop()
    w = testgui(loop)
    loop.run_until_complete(process_events(a))
#    with loop:
 #      loop.run_until_complete(w.client.run())

