from PyQt5.QtWidgets import *
from PyQt5 import QtGui
import asyncio
import time
import sys
sys.path.append('../')
from qweather import QWeatherStation


class BrokerGui(QWidget):

    def __init__(self,loop):
        super().__init__()

        self.brokerconn = "tcp://*:5559"
        self.broker = QWeatherStation(self.brokerconn,loop,debug=True,verbose=False)
        self.setWindowTitle('QWeatherStation')

        self.loop = loop
        self.initialize()
        self.loop.create_task(self.broker.async_run())

    def initialize(self):
        serverclientlist = self.make_server_client_panel()
        IPlabel = QLabel('QWeatherStation running on {:s}'.format(self.brokerconn))
        refreshbutton = QPushButton('Refresh')
        pingbutton = QPushButton('Ping')
        messagebox = QLineEdit()
        layout = QVBoxLayout()
#        toplayout = QHBoxLayout()
        #toplayout.addWidget(IPlabel)
        #toplayout.Stretch()
        #toplayout.addWidget(refreshbutton)


        layout.addWidget(IPlabel)
        layout.addWidget(refreshbutton)
        layout.addWidget(pingbutton)
        layout.addStretch()
        layout.addWidget(serverclientlist)
        layout.addWidget(messagebox)

        pingbutton.pressed.connect(self.ping_stuff)
        refreshbutton.pressed.connect(self.populate_serverlist)
        refreshbutton.pressed.connect(self.populate_clientlist)
        self.setLayout(layout)
        self.show()

    def ping_clicked(self):
        self.loop.ensure_future(self.ping_stuff())

    async def ping_stuff(self):
        self.broker.ping()
        await asyncio.sleep(2)
        self.broker.check_ping()




    def make_server_client_panel(self):
        panel = QFrame()
        self.serverlist = QTextEdit()
        self.serverlabel = QLabel('Servers')
        self.serverlist.setReadOnly(True)
        self.clientlist = QTextEdit()
        self.clientlist.setReadOnly(True)
        self.clientlabel = QLabel('Clients')
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
        servertext = ''
        for aserver in self.broker.servers.keys():
            servertext += aserver + '\n'
        if len(self.broker.servers) == 0:
            servertext = ' ---- No Servers Connected ----'
        self.serverlist.setText(servertext)


    def populate_clientlist(self):
        clienttext = ''
        for aclient in self.broker.clients.values():
            clienttext += aclient + '\n'
        if len(self.broker.clients) == 0:
            clienttext = ' ---- No Clients Connected ----'
        self.clientlist.setText(clienttext)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
            "Are you sure you want to quit?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            self.broker.close()
            self.loop.stop()
        else:
            event.ignore()


async def process_events(qapp):
    while True:
        await asyncio.sleep(0)
        qapp.processEvents()

def icon():
    iconstring = ["40 40 4 1","   c #FFFFFF",".  c #000000","+  c #AE7C3C","@  c #FF1E00",
                  "                                        ","                                        ","            ................            ","       .....               +.....       ","       .....               +.....       ",
                  "    .....++++              ++++.....    ","   .+++++++++            +++++++++++.   ","   .+++++++++            +++++++++++.   "," ..+++++++              +++++++++++++.. ",".++++++..             +++++++++..++++++.",
                  ".++++++..             +++++++++..++++++.",".++++++..            ++++++++++..++++++.",".++++++..      ...   +++...++++..++++++.",".++++++..      ...   +++...++++..++++++.",".++++++..      ...   +++...++++..++++++.",
                  " ..++++..            ++++++++++..++++.. "," ..++++..            ++++++++++..++++.. ","   .+++..            ++++++++++..+++.   ","   .+++..             +++++++++..+++.   ","   .+++..             +++++++++..+++.   ",
                  "   .+++..               +++++++..+++.   ","   .+++..               +++++++..+++.   ","   .+++..               +++++++..+++.   ","    ...  ...   ..........  +...  ...    ","          ..   ..........   ..          ",
                  "          ..   ..........   ..          ","          ..   ..........   ..          ","          ..      ....      ..          ","          ..      ....      ..          ","          ..      ....      ..          ",
                  "          ...              ...          ","          ...              ...          ","            ...          ...            ","             ..............             ","             ..............             ",
                  "                ..@@@@..                ","                ..@..@..                ","                ..@..@..                ","                ........                ","                                        "]
    return iconstring


if __name__=="__main__":
    a = QApplication( [sys.argv] )
    a.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(icon())))
    import ctypes
    myappid = u'mycompany.myproduct.subproduct.version' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
#    loop = QEventLoop(a)
 #   asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop()
    w = BrokerGui(loop)
    loop.run_until_complete(process_events(a))
#    with loop:
 #      loop.run_until_complete(w.client.run())

    sys.exit(a.exec_())