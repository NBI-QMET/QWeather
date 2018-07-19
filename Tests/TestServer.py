import sys
sys.path.append('../')
import time
import numpy as np
from qweather import QWeatherServer, QMethod

class Server(QWeatherServer):

    def __init__(self):
        self.QWeatherStationIP = "tcp://localhost:5559"
        self.servername = 'TestServer'
        self.verbose = True
        self.debug = True
        self.initialize_sockets()

    @QMethod
    def get_number(self,offset = 0):
        """Return a numper upon request"""
#        socket.send(b"%f" % np.random.rand())
        #time.sleep(2)
        num = (np.random.rand()+offset)
        return num

    @QMethod
    def multiply_stuff(self,a,b = None):
        """Return the multipla of a and b"""
        if b is None:
            return a*a
        else:
            return a*b



if __name__ == "__main__":
    server = Server()
    server.run()