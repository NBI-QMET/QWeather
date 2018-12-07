from .constants import *
import zmq
import pickle
import time


def QMethod(func):
    '''Decorator for exposing methods that can be called by clients'''
    func.is_client_accessible = True
    return func


class QWeatherServer:
    def initialize_sockets(self):
        if self.verbose:
            print('#########')
            print('Connecting "',self.servername,'" to QWeatherStation on IP "',self.QWeatherStationIP,'"\n')
        self.servername = self.servername.encode()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.connect(self.QWeatherStationIP)
        self.poller = zmq.Poller()
        self.poller.register(self.socket,zmq.POLLIN)
        self.ping_broker()
        if self.verbose:
            print('Connection established\n')

#        self.broadcastsocket = self.context.socket(zmq.PUB)
 #       self.broadcastsocket.connect(broadcastsocket)


        self.methoddict = {func:getattr(self,func) for func in dir(self) if getattr(getattr(self,func),'is_client_accessible',False)}
        self.register_at_station()

    def ping_broker(self):
        if self.debug:
            print('DEBUG(',self.servername.decode(),'): Sending ping:\n',[b'P'],'\n\n')
        self.send_message([b'',b'P'])
        try:
            if len(self.poller.poll(timeout=5000)) == 0: #wait 2 seconds for a ping from the server
                raise Exception('QWeatherStation not found')
            else:
                msg = self.socket.recv_multipart()
                empty = msg.pop(0)
                pong = msg.pop(0)
                if self.debug:
                    print('DEBUG(',self.servername.decode(),'): Recieved Pong: ',pong,'\n\n')
                if pong != b'b':
                    raise Exception('QWeatherStation sent wrong Pong')              

        except Exception as e:
            self.poller.unregister(self.socket)
            self.socket.close()
            raise e

    def register_at_station(self):
        self.methodlist = [(func,getattr(self,func).__doc__) for func in dir(self) if getattr(getattr(self,func),'is_client_accessible',False)]
        msg = [b'',b'S',CREADY,PSERVER,self.servername,pickle.dumps(self.methodlist)]
        if self.debug:
            print('DEBUG(',self.servername.decode(),'): To QWeatherStation:\n',msg,'\n\n')
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
        self.poller.unregister(self.socket)
        self.socket.close()

    def handle_messages(self,msg):
        if self.debug:
            print('DEBUG(',self.servername.decode(),'): From QWeatherStation:\n',msg,'\n\n')
        empty = msg.pop(0)
        assert empty == b''
        command = msg.pop(0)

        if command == CREQUEST:
            messageid = msg.pop(0)
            client = msg.pop(0)
            fnc = msg.pop(0).decode()
            args,kwargs = pickle.loads(msg.pop(0))
            if self.debug:
                print('DEBUG(',self.servername.decode(),'): Calling function:\n',fnc,' with arguments:\n',args,kwargs,'\n\n')
            answ = self.methoddict[fnc](*args,**kwargs)
            answ = [empty,b'S',CREPLY] + [messageid,self.servername,client,pickle.dumps(answ)]
            if self.debug:
                print('DEBUG(',self.servername.decode(),'): To QWeatherStation:\n', answ,'\n\n')
            self.send_message(answ)        

        elif command == CREADY+CSUCCESS:
            if self.verbose:
                print('\nMethods registered at QWeatherStation. (',[i[0] for i in self.methodlist],')')

        elif command == CREADY+CFAIL:
            raise Exception(msg.pop(0).decode())

        elif command == CPING:
            ping = msg.pop(0)
            if ping != b'P':
                raise Exception('QWeatherStation sent wrong ping')
            if self.debug:
                print('DEBUG(',self.servername.decode(),': Recieved Ping from QWeatherStation','\n\n')
            self.send_message([b'',b'b'])

    def send_message(self,msg):
        self.socket.send_multipart(msg)
        

        

    def initialize_broadcasting(self):
        if self.debug:
            print('DEBUG(',self.servername.decode(),'): Initializing broadcasting')
