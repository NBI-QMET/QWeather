from .constants import QConstants
import zmq
import pickle
def QMethod(func):
    '''Decorator for exposing methods that can be called by clients'''
    func.is_client_accessible = True
    return func


class QWeatherServer:
    def initialize_sockets(self):
        if self.verbose:
            print('#########')
            print('Connecting "',self.servername,'" to QWeatherStation on IP "',self.QWeatherStationIP,'"\n')
        self.QConstant = QConstants()
        self.servername = self.servername.encode()
        self.context = zmq.Context()
        self.QWeatherStation = self.context.socket(zmq.DEALER)
        self.QWeatherStation.connect(self.QWeatherStationIP)
        if self.verbose:
            print('Connection established\n')

#        self.broadcastsocket = self.context.socket(zmq.PUB)
 #       self.broadcastsocket.connect(broadcastsocket)

        self.poller = zmq.Poller()
        self.poller.register(self.QWeatherStation,zmq.POLLIN)

        self.methoddict = {func:getattr(self,func) for func in dir(self) if getattr(getattr(self,func),'is_client_accessible',False)}
        self.register_at_station()


    def register_at_station(self):
        methodlist = [(func,getattr(self,func).__doc__) for func in dir(self) if getattr(getattr(self,func),'is_client_accessible',False)]
        msg = [b'','S{:s}'.format(self.QConstant.command_ready).encode(),'QWPS01'.encode(),self.servername,pickle.dumps(methodlist)]
        if self.debug:
            print('DEBUG: To QWeatherStation: ',msg)
        self.QWeatherStation.send_multipart(msg)

        if self.verbose:
            print('\nMethods registered at QWeatherStation. (',[i[0] for i in methodlist],')')

    def run(self):
        #Broadcast method information
        
        while True:
            try:
                items = self.poller.poll(1000)
                if items:
                    msg = self.QWeatherStation.recv_multipart()
                    self.handle_messages(msg)
            except KeyboardInterrupt:
                break


    def handle_messages(self,msg):
        if self.debug:
            print('DEBUG: From QWeatherStation: ',msg)
        client = msg.pop(0)
        empty = msg.pop(0)
        assert empty == b''
        fnc = msg.pop(0).decode()
        args,kwargs = pickle.loads(msg.pop(0))
        if self.debug:
            print('DEBUG: Calling function: ',fnc,' with arguments: ',args,kwargs)
        answ = self.methoddict[fnc](*args,**kwargs)
        answ = [empty,'S{:s}'.format(self.QConstant.command_reply).encode()] + [self.servername,client,pickle.dumps(answ)]
        if self.debug:
            print('DEBUG: To QWeatherStation: ', answ)
        self.QWeatherStation.send_multipart(answ)