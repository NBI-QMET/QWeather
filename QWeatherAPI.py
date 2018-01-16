
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


class QConstants:
    """Constants used for the servers, clients and brokers"""

    protocol_server = 'QWPS01' #Server following majordomopatternv 0.1
    protocol_client = 'QWPC01' #Client following majordomopatternv 0.1
    command_ready = '1'
    command_request = '2'
    command_reply = '3'
    command_disconnect = '4'
        

class QWeatherStation:

    def __init__(self,IP,verbose=False,debug = False):
        self.StationIP = IP
        self.verbose = verbose
        self.debug = debug
        self.servers = {}
        self.clients = []
        self.QConstant = QConstants()
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
                empty = msg.pop(0)
                assert empty == b''
                command = msg.pop(0).decode() # 0xFx for server and 0x0x for client
                if command[0] == 'S': #server
                    self.process_server(sender,command[1],msg)
                elif (command[0] == 'C'): #client
                    self.process_client(sender,command[1],msg)

                else:
                    if self.verbose:
                        print('Invalid message')

    def process_client(self,sender,command,msg):
        if command == self.QConstant.command_ready:
            version = msg.pop(0).decode()
            if not version == self.QConstant.protocol_client:
                msg = [sender,b'',b'Protocol error']
            else:
                msg = [sender,b''] + [pickle.dumps(self.servers)]
                if self.verbose:
                    print('Client ready at "',int.from_bytes(sender,byteorder='big'),'"')
            self.socket.send_multipart(msg)

        elif command == self.QConstant.command_request:
            server = msg.pop(0).decode()
            serveraddr = self.servers[server][0]
            msg = [serveraddr,sender,b''] + msg
            self.socket.send_multipart(msg)
            if self.debug:
                print('DEBUG: CLient request at"',sender,'":',msg)




    def process_server(self,sender,command,msg):
        if command == self.QConstant.command_ready:
            version = msg.pop(0).decode()
            if not version == self.QConstant.protocol_server:
                msg = [sender,b'',b'Protocol error']
                self.socket.send_multipart(msg)
            else:
                servername = msg.pop(0).decode()
                servermethods = pickle.loads(msg.pop(0))
                self.servers[servername] = (sender,servermethods)
                if self.verbose:
                    print('Server "',servername,'" ready at: "',int.from_bytes(sender,byteorder='big'),'"')

        elif command == self.QConstant.command_reply:
            server = msg.pop(0)
            client = msg.pop(0)
            answ = msg.pop(0)
            msg = [client,b'',server,answ]
            self.socket.send_multipart(msg)
            if self.debug:
                print('DEBUG: To "',client,'"',msg)




from zmq.asyncio import Context, Poller
import asyncio
class QWeatherClient:

    class serverclass:
        def __init__(self,name,addr,methods,client):
            self.name = name
            self.addr = addr
            self.client = client
            for amethod in methods:
                setattr(self,amethod[0],self.bindingfunc(amethod[0],amethod[1]))


        def bindingfunc(self,methodname,methoddoc):
            def func(*args,**kwargs):
                return self.client.send_request([self.name.encode(),methodname.encode(),pickle.dumps([args,kwargs])])
            func.__name__ = methodname
            func.__doc__ = methoddoc
            func.is_remote_server_method = True
            return func


        def __repr__(self):
            msg = ""
            lst = [getattr(self,method) for method in dir(self) if getattr(getattr(self,method),'is_remote_server_method',False)]
            if len(lst) == 0:
                return 'No servers connected'
            else:
                for amethod in lst:
                    msg += amethod.__name__ +"\n"
            return msg.strip()
    

    context = None
    socket = None
    poller = None
    futureobjectdict = {}

    def __init__(self,QWeatherStationIP,loop = None):
        self.QConstant = QConstants()
        self.QWeatherStationIP = QWeatherStationIP
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop
        self.reconnect()
        self.loop.run_until_complete(self.get_server_info())
        self.running = False



    def reconnect(self):
        '''connects or reconnects to the broker'''
        if self.poller:
            self.poller.unregister(self.socket)
        if self.socket: 
            self.socket.close()
        if self.context:
            self.context.term()
        self.context = Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.connect(self.QWeatherStationIP)
        self.serverlist = []
        self.poller = Poller()
        self.poller.register(self.socket,zmq.POLLIN)
        #lol = asyncio.ensure_future()
        

    async def get_server_info(self):
        msg = [b'','C{:s}'.format(self.QConstant.command_ready).encode(),self.QConstant.protocol_client.encode(),]
        #print('sending')
        self.send_message(msg)
        msg =  await self.socket.recv_multipart()
        empty = msg.pop(0)
        assert empty == b''
        for name,items in pickle.loads(msg.pop(0)).items():
            addr = items[0]
            methods = items[1]
            server = self.serverclass(name,addr,methods,self)
            server.is_remote_server = True
            setattr(self,name,server)
            

#                _method = 
 #               _method = methodclass(self.send_request,server.name,amethod[0],amethod[1])
  #              _method.is_remote_server_method = True
   #             setattr(server,amethod[0],_method)
        #print('loaded servers')
        return None

    def send_request(self,body):
        if self.running:
            result =  asyncio.get_event_loop().create_task(self.async_send_request(body))
        else:
            result = self.sync_send_request(body)
        return result

    def sync_send_request(self,body):
        msg = [b'','C{:s}'.format(self.QConstant.command_request).encode()] + body
        server = body[0]
        self.send_message(msg)
        msg = self.loop.run_until_complete(self.socket.recv_multipart())
        empty = msg.pop(0)
        assert empty == b''
        server = msg.pop(0)
        answ = pickle.loads(msg[0])
        return answ

    async def async_send_request(self,body):
        print('async send request')
        msg = [b'','C{:s}'.format(self.QConstant.command_request).encode()] + body
        server = body[0]
        #print(body)
        self.send_message(msg)
        answ = await self.recieve_message(server)
        return answ
       # return msg

    def send_message(self,msg):
        #self.loop.create_task(self.socket.send_multipart(msg))
        self.socket.send_multipart(msg)


    def recieve_message(self,servername):
        tmp = self.loop.create_future()
        self.futureobjectdict[servername] = tmp
        #print('went here')
        return tmp

        #ans =self.loop.create_task(self.socket.recv_multipart())

#        ans = await self.socket.recv_multipart()
  #      return ans


    async def run(self):
        self.running = True
        while True:
            try:
                #print('polling')
                items = await self.poller.poll(1000)
                if items:
                    msg = await self.socket.recv_multipart()
                    print('recieved',msg)
                    empty = msg.pop(0)
                    assert empty == b''
                    server = msg.pop(0)
                    #print(server)
                    #print(self.futureobjectdict)
                    msg = pickle.loads(msg[0])
                    #print(msg)
                    self.futureobjectdict[server].set_result(msg)

                    #print(msg)
            except KeyboardInterrupt:
                break
                #self.socket.close()
                #self.context.term()



    def __repr__(self):
        #self.get_server_info()
        msg = ""
        lst = [getattr(self,server) for server in dir(self) if getattr(getattr(self,server),'is_remote_server',False)]
        if len(lst) == 0:
            return 'No servers connected'
        else:
            for aserver in lst:
                msg += aserver.name + "\n"
        return msg.strip()


if __name__ == "__main__":
    server = Server()
    server.run()