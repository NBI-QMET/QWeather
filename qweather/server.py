from .constants import *
import zmq
import pickle
import time
import re
import logging
import traceback
import atexit

def QMethod(func):
    '''Decorator for exposing methods that can be called by clients'''
    func.is_client_accessible = True
    return func


class QWeatherServer:

    def __init__(self,verbose=False,debug=False):
        pass

    def initialize_sockets(self):
        formatting = '{:}: %(levelname)s: %(message)s'.format(self.servername)
        if self.debug:
            logging.basicConfig(format=formatting,level=logging.DEBUG)
        if self.verbose:
            logging.basicConfig(format=formatting,level=logging.INFO)
        
        logging.info('#########\n Connecting {:} to QWeatherStation on IP: {:}'.format(self.servername,self.QWeatherStationIP))
        self.servername = self.servername.encode()
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
        #self.ping_broker()
        logging.info('Connection established')


        self.methoddict = {func:getattr(self,func) for func in dir(self) if getattr(getattr(self,func),'is_client_accessible',False)}
        self.register_at_station()
        atexit.register(self.close)

    def ping_broker(self):
        logging.debug('Sending ping')
        self.send_message([b'',b'P'])
        try:
            if len(self.poller.poll(timeout=5000)) == 0: #wait 2 seconds for a ping from the server
                raise Exception('QWeatherStation not found')
            else:
                msg = self.socket.recv_multipart()
                empty = msg.pop(0)
                pong = msg.pop(0)
                logging.debug('Recieved Pong')
                if pong != b'b':
                    raise Exception('QWeatherStation sent wrong Pong')              

        except Exception as e:
            self.poller.unregister(self.socket)
            self.socket.close()
            raise e

    def register_at_station(self):
        self.methodlist = [(func,getattr(self,func).__doc__) for func in dir(self) if getattr(getattr(self,func),'is_client_accessible',False)]
        msg = [b'',b'S',CREADY,PSERVER,self.servername,pickle.dumps(self.methodlist)]
        logging.debug('To QWeatherStation:\n{:}'.format(msg))
        self.send_message(msg)


    def run(self):
        while True:
            try:
                items = self.poller.poll(1000)
                if items:
                    msg = self.socket.recv_multipart()
                    self.handle_messages(msg)
            except KeyboardInterrupt:
                self.close()
                break

    def close(self):
        self.send_message([b'',b'S',SDISCONNECT] + [self.servername])
        self.poller.unregister(self.socket)
        self.socket.close()

    def handle_messages(self,msg):
        logging.debug('From QWeatherStation:\n{:}'.format(msg))
        empty = msg.pop(0)
        assert empty == b''
        command = msg.pop(0)

        if command == CREQUEST:
            messageid = msg.pop(0)
            client = msg.pop(0)
            fnc = msg.pop(0).decode()
            args,kwargs = pickle.loads(msg.pop(0))
            logging.debug('Calling Function {:} with arguments {:},{:}'.format(fnc,args,kwargs))
            try:
                answ = self.methoddict[fnc](*args,**kwargs)
            except Exception as e:
                traceback.print_exc()
                answ = Exception('Call failed on server')
                
            answ = [empty,b'S',CREPLY] + [messageid,client,pickle.dumps(answ)]
            logging.debug('To QWeatherStation:\n{:}'.format(answ))
            self.send_message(answ)        

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

    def send_message(self,msg):
        self.socket.send_multipart(msg)

    def broadcast(self,msg):
        self.pubsocket.send_multipart([self.servername, pickle.dumps(msg)])

