from PyQt5.QtWidgets import *
from PyQt5 import QtGui
from quamash import QEventLoop, QThreadExecutor
import asyncio
from QWeatherAPI import QWeatherClient


class testgui(QWidget):

    def __init__(self,loop):
        super().__init__()

        self.setWindowTitle('Test GUI')

        self.initialize()
        brokerconn = "tcp://localhost:5559"
        self.client = QWeatherClient(brokerconn,loop)
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

        sendbutton.pressed.connect(lambda : self.send_command(self.client.TestServer.get_number(),l1))
        sendbutton2.pressed.connect(lambda : self.send_command(self.client.TestServer2.get_number(),l2))
        self.setLayout(layout)
        self.show()


    def send_command(self,func,label):

        self.loop.create_task(self.blocking_call(func,label))
#       yield ans
        #print(ans)

    async def blocking_call(self,func,label):
        a = await func 
        label.setText(a.decode())
#        return a


async def process_events(qapp):
    while True:
        await asyncio.sleep(0)
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

