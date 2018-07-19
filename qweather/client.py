from .constants import *
import zmq
import pickle
from zmq.asyncio import Context, Poller
import asyncio
import time
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
                wait = kwargs.pop('wait',True)
                if wait:
                    return self.client.send_request([self.name.encode(),methodname.encode(),pickle.dumps([args,kwargs])])
                else:
                    self.client.send_request([self.name.encode(),methodname.encode(),pickle.dumps([args,kwargs])],wait=False)
                    return None


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

    def __init__(self,QWeatherStationIP,name = None,loop = None):
        self.QWeatherStationIP = QWeatherStationIP
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop

        if name is None:
            import socket
            name = socket.gethostname()
        self.name = name.encode()
        self.reconnect()
        self.ping_broker()
        self.loop.run_until_complete(self.get_server_info())
        self.running = False
        self.messageid = 0




    def reconnect(self):
        '''connects or reconnects to the broker'''
        if self.poller:
            self.poller.unregister(self.socket)
        if self.socket: 
            self.socket.close()
        self.context = Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.connect(self.QWeatherStationIP)
        self.poller = Poller()
        self.poller.register(self.socket,zmq.POLLIN)
        
    
    async def get_server_info(self):
        msg = [b'',b'C',CREADY,PCLIENT,self.name]
        self.send_message(msg)
        msg =  await self.socket.recv_multipart()
        empty = msg.pop(0)
        assert empty == b''
        command = msg.pop(0)
        self.serverlist = []
        if command == CREADY + CFAIL:
            raise Exception(msg.pop(0).decode())
        else:
            for name,items in pickle.loads(msg.pop(0)).items():
                addr = items[0]
                methods = items[1]
                server = self.serverclass(name,addr,methods,self)
                server.is_remote_server = True
                setattr(self,name,server)
                self.serverlist.append(server)
        return None

    def ping_broker(self):
        pass
        '''
        self.send_message([b'',b'P'])
        try:
            if len(self.loop.run_until_complete(self.poller.poll(timeout=2000))) == 0: #wait 2 seconds for a ping from the server
                raise Exception('QWeatherStation not found')
            else:
                msg =  self.loop.run_until_complete(self.socket.recv_multipart())
                empty = msg.pop(0)
                pong = msg.pop(0)
                if pong != b'b':
                    raise Exception('QWeatherStation sent wrong Pong')              

        except Exception as e:
            self.poller.unregister(self.socket)
            self.socket.close()
            raise e
        '''

    def send_request(self,body,wait=True):
        self.messageid+=1
        if self.messageid > 255:
            self.messageid = 0
        if wait:
            if self.running:
                result =  asyncio.get_event_loop().create_task(self.async_send_request(body,self.messageid.to_bytes(1,'big')))
            else:
                result = self.sync_send_request(body,self.messageid.to_bytes(1,'big'))
            return result
        else:
            #self.sync_send_request(body,self.messageid.to_bytes(1,'big'),wait=False)
            asyncio.get_event_loop().create_task(self.async_send_request(body,self.messageid.to_bytes(1,'big')))

    def sync_send_request(self,body,ident,wait=False):
        msg = [b'',b'C',CREQUEST,ident]  + body
        server = body[0]
        self.send_message(msg)
        if wait:
            msg = self.loop.run_until_complete(self.socket.recv_multipart())
            empty = msg.pop(0)
            assert empty == b''
            command = msg.pop(0)
            ident = msg.pop(0)
            server = msg.pop(0)
            answ = pickle.loads(msg[0])
            return answ
    
    async def async_send_request(self,body,ident):
        server = body[0]
        msg = [b'',b'C',CREQUEST,ident]  + body
        self.send_message(msg)
        answ = await self.recieve_message(ident+server)
        self.futureobjectdict.pop(ident+server)
        return answ

    def send_message(self,msg):
        self.socket.send_multipart(msg)


    def recieve_message(self,ident):
        tmp = self.loop.create_future()
        self.futureobjectdict[ident] = tmp
        return tmp

    async def run(self):
        self.running = True
        while True:
            try:
                items = await self.poller.poll(1000)
                if items:
                    msg = await self.socket.recv_multipart()
                    empty = msg.pop(0)
                    assert empty == b''
                    command = msg.pop(0)
                    if command == CREQUEST + CSUCCESS:
                        messageid = msg.pop(0)
                        server = msg.pop(0)
                        msg = pickle.loads(msg[0])
                        self.futureobjectdict[messageid + server].set_result(msg)
                    elif command == CREQUEST + CFAIL:
                        messageid = msg.pop(0)
                        server = msg.pop(0)
                        self.futureobjectdict[messageid+server].set_exception(Exception(msg.pop(0)))

            except KeyboardInterrupt:
                self.close()
                break
    
    def close(self):
        self.poller.unregister(self.socket)
        self.socket.close()



    def __repr__(self):
        msg = ""
        if len(self.serverlist) == 0:
            return 'No servers connected'
        else:
            for aserver in self.serverlist:
                msg += aserver.name + "\n"
        return msg.strip()

    def __iter__(self):
        return (aserv for aserv in self.serverlist)

    def __getitem__(self,key):
        return self.serverlist[key]