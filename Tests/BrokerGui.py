from PyQt5.QtWidgets import *
from PyQt5 import QtGui
from quamash import QEventLoop, QThreadExecutor
import asyncio
import sys
sys.path.append('../')
from qweather import QWeatherStation


class BrokerGui(QWidget):

    def __init__(self,loop):
        super().__init__()

        self.brokerconn = "tcp://*:5559"
        self.broker = QWeatherStation(self.brokerconn,loop)
        self.setWindowTitle('QWeatherStation')

        self.initialize()
        self.loop = loop
        self.loop.create_task(self.broker.async_run())

    def initialize(self):
        serverclientlist = self.make_server_client_panel()
        IPlabel = QLabel('QWeatherStation running on {:s}'.format(self.brokerconn))
        refreshbutton = QPushButton('Refresh')
        messagebox = QLineEdit()
        layout = QVBoxLayout()
#        toplayout = QHBoxLayout()
        #toplayout.addWidget(IPlabel)
        #toplayout.Stretch()
        #toplayout.addWidget(refreshbutton)


        layout.addWidget(IPlabel)
        layout.addWidget(refreshbutton)
        layout.addStretch()
        layout.addWidget(serverclientlist)
        layout.addWidget(messagebox)

        refreshbutton.pressed.connect(self.populate_serverlist)
        refreshbutton.pressed.connect(self.populate_clientlist)
        self.setLayout(layout)
        self.show()


    def make_server_client_panel(self):
        panel = QFrame()
        self.serverlist = QFrame()
        self.clientlist = QFrame()
        self.serverlist.setLayout(QVBoxLayout())
        self.clientlist.setLayout(QVBoxLayout())
        panellayout = QHBoxLayout()
        panellayout.addWidget(self.serverlist)
        panellayout.addWidget(self.clientlist)
        panel.setLayout(panellayout)
        self.populate_serverlist()
        self.populate_clientlist()
        return panel

    def populate_serverlist(self):
        self.clearLayout(self.serverlist.layout())
        for aserver in self.broker.servers.keys():
            alabel = QLabel("{:s}".format(aserver))
            self.serverlist.layout().addWidget(alabel)
        if self.serverlist.layout().count() == 0:
            self.serverlist.layout().addWidget(QLabel(' ---- No Servers Connected ----'))


    def populate_clientlist(self):
        self.clearLayout(self.clientlist.layout())
        for aserver in self.broker.clients:
            alabel = QLabel("{:s}".format(aserver))
            self.clientlist.layout().addWidget(alabel)
        if self.clientlist.layout().count() == 0:
            self.clientlist.layout().addWidget(QLabel(' ---- No Clients Connected ----'))

    def clearLayout(self,layout):
      while layout.count():
        child = layout.takeAt(0)
        if child.widget():
          child.widget().deleteLater()

async def process_events(qapp):
    while True:
        await asyncio.sleep(0)
        qapp.processEvents()



if __name__=="__main__":
    a = QApplication( [] )
#    loop = QEventLoop(a)
 #   asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop()
    w = BrokerGui(loop)
    loop.run_until_complete(process_events(a))
#    with loop:
 #      loop.run_until_complete(w.client.run())

