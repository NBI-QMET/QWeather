from .constants import QConstants
import zmq
import pickle
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