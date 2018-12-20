import sys
sys.path.append('../')
import time
import numpy as np
from qweather import QWeatherServer, QMethod
import asyncio

class Server(QWeatherServer):

    def __init__(self):
        super().__init__()
        self.QWeatherStationIP = "tcp://localhost:5559"
        self.servername = 'TestServer'
        self.verbose = False
        self.debug = False
        self.initialize_sockets()

    @QMethod
    def get_number(self,offset = 0):
        """Return a numper upon request"""
#        socket.send(b"%f" % np.random.rand())
        time.sleep(1)
        num = (np.random.rand()+offset)
        return num

    @QMethod
    def multiply_stuff(self,a,b = None):
        """Return the multipla of a and b"""
        if b is None:
            return a*a
        else:
            return a*b

    @QMethod
    def ping(self):
        self.ping_broker()

    @QMethod
    def do_something_scheduled(self):
        for i in range(10):
            num = np.random.rand(5)
            print('broadcasting ',num)
            self.broadcast(num)



if __name__ == "__main__":
    server = Server()
    server.run()
