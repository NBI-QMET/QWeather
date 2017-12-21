
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
        msg = [b'',b'MDPS01',0xf0.to_bytes(1,'big'),self.servername,pickle.dumps(methodlist)]
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
        answ = [empty,b'MDPS01',0xf2.to_bytes(1,'big')] + [self.servername,client,pickle.dumps(answ)]
        if self.debug:
            print('DEBUG: To QWeatherStation: ', answ)
        self.QWeatherStation.send_multipart(answ)


class QWeatherStation:

    serverheader = b'MDPS01' #Server following majordomopatternv 0.1
    clientheader = b'MDPC01' #Client following majordomopatternv 0.1
    clientready = 0x00
    clientrequest = 0x01
    clientreply = 0x02
    clientdisconnect = 0x03
    serverready = 0xf0
    serverrequest = 0xf1
    serverreply = 0xf2
    serverdisconnect = 0xf3


    def __init__(self,IP,verbose=False,debug = False):
        self.StationIP = IP
        self.verbose = verbose
        self.debug = debug
        self.servers = {}
        self.clients = []
        self.cnx = zmq.Context()
        self.socket = self.cnx.socket(zmq.ROUTER)
        self.poller = zmq.Poller()
        self.poller.register(self.socket,zmq.POLLIN)
        self.socket.bind(self.StationIP)
        if self.verbose:
            print('QWeatherStation ready to run on IP: "',self.StationIP,'"')

    def run(self):


        while True:
            try:
                items = self.poller.poll(1000)
            except KeyboardInterrupt:
                break

            if items:
                msg = self.socket.recv_multipart()

                sender = msg.pop(0)
                if self.debug:
                    print('DEBUG: From "',sender,'": ',msg)
                delim = msg.pop(0)
                assert delim == b''
                header = msg.pop(0)
                if (header == self.serverheader):
                    self.process_server(sender,msg)
                elif (header == self.clientheader):
                    self.process_client(sender,msg)

                else:
                    if self.verbose:
                        print('Invalid message')

    def process_client(self,sender,msg):
        command = int.from_bytes((msg.pop(0)),byteorder='big')
        if command == self.clientready:
            msg = [sender,b''] + [pickle.dumps(self.servers)]
            self.socket.send_multipart(msg)
            if self.verbose:
                print('Client ready at "',int.from_bytes(sender,byteorder='big'),'"')

        elif command == self.clientrequest:
            server = msg.pop(0).decode()
            serveraddr = self.servers[server][0]
            msg = [serveraddr,sender,b''] + msg
            self.socket.send_multipart(msg)
            if self.debug:
                print('DEBUG: CLient request at"',sender,'":',msg)




    def process_server(self,sender,msg):
        command = int.from_bytes((msg.pop(0)),byteorder='big')
        if command == self.serverready:
            servername = msg.pop(0).decode()
            servermethods = pickle.loads(msg.pop(0))
            self.servers[servername] = (sender,servermethods)
            if self.verbose:
                print('Server "',servername,'" ready at: "',int.from_bytes(sender,byteorder='big'),'"')
            ##self.socket.send_multipart([sender,b'',b'nothing'])
        elif command == self.serverreply:
            server = msg.pop(0)
            client = msg.pop(0)
            answ = msg.pop(0)
            msg = [client,b'',server,answ]
            self.socket.send_multipart(msg)
            if self.debug:
                print('DEBUG: To "',client,'"',msg)


if __name__ == "__main__":
    server = Server()
    server.run()