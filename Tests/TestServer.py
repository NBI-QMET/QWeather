import sys
sys.path.append('../')
import time
import numpy as np
from qweather import QWeatherServer, QMethod
import asyncio

class Server(QWeatherServer):

    def __init__(self,name='Testserver',verbose=True,debug=False):
        self.QWeatherStationIP = "tcp://localhost:5559"
<<<<<<< HEAD
        self.servername = 'TestServer'
        self.verbose = True
        self.debug = False
=======
        self.servername = name
        self.verbose = verbose
        self.debug = debug
        super().__init__()
>>>>>>> develop
        self.initialize_sockets()

    @QMethod
    def get_number(self):
        """Returns the number 2"""
        return 2

    @QMethod
    def crashing_function(self):
        """Does an illegal division by zero and crashes the server"""
        1/0
        return

    @QMethod
    def very_long_function(self):
        """Waits for 6 seconds before returning"""
        time.sleep(6)
        return 2


    @QMethod
    def ping(self):
        self.ping_broker()

    @QMethod
    def do_something_scheduled(self,sleeptime=None):
        for i in range(10):
            num = np.random.rand(5)
            print('broadcasting ',num)
            self.broadcast(num)
            if sleeptime is not None:
                time.sleep(sleeptime)

    @QMethod
    def long_operation(self,delaytime):
        '''Delays for a number of seconds specified by delaytime'''
        time.sleep(delaytime)
        response ='Testserver1 is done'
        print(response)
        #return response



if __name__ == "__main__":
    import argparse
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument('--verbose', action='store_true')
    my_parser.add_argument('--debug', action='store_true')
    my_parser.add_argument('name', nargs = '?')

    args = vars(my_parser.parse_args())
    server = Server(name=args['name'],verbose=args['verbose'],debug = args['debug'])
    
    server.run()
