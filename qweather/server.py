"""
The client class of qweather\n
This is what connects to hardware, or performs operations.
Only functions with the "QMethod" decorator are exposed to the clients (users)
"""

from .constants import *
import zmq
import pickle
import time
import re
import logging
import traceback
import atexit

def QMethod(func):
    """Decorator for exposing methods that can be called by clients"""
    func.is_client_accessible = True
    return func

class QWeatherServer:
    """Base class for qweather server"""

    def initialize_sockets(self):
        """Setup the sockets for communication"""
        self.servername = self.servername.encode()
        formatting = '{:}: %(levelname)s: %(message)s'.format(self.servername)
        if self.debug:
            logging.basicConfig(format=formatting,level=logging.DEBUG)
        if self.verbose:
            logging.basicConfig(format=formatting,level=logging.INFO)
        pass
        atexit.register(self.close)        

        logging.info('#########\n Connecting {:} to QWeatherStation on IP: {:}'.format(self.servername,self.QWeatherStationIP))
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)

        IpAndPort = re.search(IPREPATTERN,self.QWeatherStationIP)
        assert IpAndPort != None, 'Ip not understood (tcp://xxx.xxx.xxx.xxx:XXXX or txp://localhost:XXXX)'
        self.QWeatherStationIP = IpAndPort.group(1)
        self.QWeatherStationSocket = IpAndPort.group(2)
        assert self.QWeatherStationIP[:6] == 'tcp://', 'Ip not understood (tcp://xxx.xxx.xxx.xxx:XXXX or txp://localhost:XXXX)'
        assert len(self.QWeatherStationSocket) == 4, 'Port not understood (tcp://xxx.xxx.xxx.xxx:XXXX or txp://localhost:XXXX)'
        
        self.socket.connect(self.QWeatherStationIP + ':' + self.QWeatherStationSocket)
        self.pubsocket = self.context.socket(zmq.PUB)
        self.pubsocket.connect(self.QWeatherStationIP + ':' + str(int(self.QWeatherStationSocket) + PUBLISHSOCKET))
        self.poller = zmq.Poller()
        self.poller.register(self.socket,zmq.POLLIN)
        logging.info('Connection established')


        self.methoddict = {func:getattr(self,func) for func in dir(self) if getattr(getattr(self,func),'is_client_accessible',False)}
        self.register_at_broker()

    def ping_broker(self):
        """Ping the broker, with a timeout of 5 s"""
        logging.debug('Sending ping')
        self.send_message([b'',b'P'])
        try:
            if len(self.poller.poll(timeout=5000)) == 0: #wait 5 seconds for a ping from the server
                raise Exception('QWeatherStation not found')
            else:
                msg = self.recieve_message()
                empty = msg.pop(0)
                pong = msg.pop(0)
                logging.debug('Recieved Pong')
                if pong != b'b':
                    raise Exception('QWeatherStation sent wrong Pong')              

        except Exception as e:
            self.poller.unregister(self.socket)
            self.socket.close()
            raise e

    def register_at_broker(self):
        """Register the server at the broker"""
        self.methodlist = [(func,getattr(self,func).__doc__) for func in dir(self) if getattr(getattr(self,func),'is_client_accessible',False)]
        msg = [b'',b'S',CREADY,PSERVER,self.servername,pickle.dumps(self.methodlist)]
        logging.debug('To QWeatherStation:\n{:}'.format(msg))
        self.send_message(msg)


    def run(self):
        """Run the server, by repeatedly polling the incoming socket"""
        while True:
            try:
                items = self.poller.poll(1000)
                if items:
                    msg = self.recieve_message()
                    self.handle_messages(msg)
            except KeyboardInterrupt:
                self.close()
                break

    def recieve_message(self):
        """Recieve a multi-frame-message"""
        msg = self.socket.recv_multipart()
        return msg

    def close(self):
        """Closing func, called on shutdown (not terminal close or force kill)"""
        self.send_message([b'',b'S',SDISCONNECT] + [self.servername])
        self.poller.unregister(self.socket)
        self.socket.close()

    def handle_messages(self,msg):
        """Handle messages from the broker"""
        logging.debug('From QWeatherStation:\n{:}'.format(msg))
        empty = msg.pop(0)
        assert empty == b''
        command = msg.pop(0)

        if command == CREQUEST:
            messageid = msg.pop(0)
            client = msg.pop(0)
            self.handle_request(messageid,client,msg)

        elif command == CREADY+CSUCCESS:
             logging.info('Methods registered at QWeatherStation. ({:})'.format([i[0] for i in self.methodlist]))

        elif command == CREADY+CFAIL:
            raise Exception(msg.pop(0).decode())

        elif command == CPING:
            ping = msg.pop(0)
            if ping != b'P':
                raise Exception('QWeatherStation sent wrong ping')
            logging.debug('Recieved Ping from QWeatherStation')
            self.send_message([b'',b'b'])

    def handle_request(self,messageid,client,msg):
        """Handle a request from a client"""
        fnc = msg.pop(0).decode()
        args,kwargs = pickle.loads(msg.pop(0))
        logging.debug('Calling Function {:} with arguments {:},{:}'.format(fnc,args,kwargs))
        try:
            answ = self.methoddict[fnc](*args,**kwargs)
        except Exception as e:
            traceback.print_exc()
            answ = Exception('Call failed on server')            
        answ = [b'',b'S',CREPLY] + [messageid,client,pickle.dumps(answ)]
        logging.debug('To QWeatherStation:\n{:}'.format(answ))
        self.send_message(answ)        


    def send_message(self,msg):
        """Send a multi-frame message"""
        self.socket.send_multipart(msg)

    def broadcast(self,msg):
        """Broadcast a multi-frame-message"""
        self.pubsocket.send_multipart([self.servername, pickle.dumps(msg)])

