import zmq
import time
import pickle
from zmq.asyncio import Context, Poller
import asyncio

class serverclass:
    def __init__(self,name,addr,methods):
        self.name = name
        self.addr = addr

    def __repr__(self):
        msg = ""
        lst = [getattr(self,method) for method in dir(self) if getattr(getattr(self,method),'is_remote_server_method',False)]
        if len(lst) == 0:
            return 'No servers connected'
        else:
            for amethod in lst:
                msg += amethod.__name__ +"\n"
        return msg.strip()

class methodclass:
    def __init__(self,func,servername,name,doc):
        self.func = func
        self.servername = servername
        #  lets copy some key attributes from the original function
        self.__name__ = name
        self.__doc__ = doc

    def __call__(self, *args, **kwargs):
        msg = [self.servername.encode(),self.__name__.encode()]
        msg += [pickle.dumps([args,kwargs])]
        #print(msg)
        return self.func(msg)

    def __repr__(self):
        return self.__doc__

class QWeatherClient:
    context = None
    socket = None
    poller = None
    futureobjectdict = {}

    def __init__(self,QWeatherStationIP,loop):
        self.QWeatherStationIP = QWeatherStationIP
        self.loop = loop
        self.reconnect()

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
#        self.loop.ensure_future(self.get_server_info())

    async def get_server_info(self):
        msg = [b'',b'MDPC01',0x00.to_bytes(1,'big')]
        #print('sending')
        self.send_message(msg)
        msg = await self.socket.recv_multipart()
        empty = msg.pop(0)
        assert empty == b''
        for name,items in pickle.loads(msg.pop(0)).items():
            addr = items[0]
            methods = items[1]
            server = serverclass(name,addr,methods)
            server.is_remote_server = True
            setattr(self,name,server)
            for amethod in methods:
                _method = methodclass(self.send_request,server.name,amethod[0],amethod[1])
                _method.is_remote_server_method = True
                setattr(server,amethod[0],_method)
        #print('loaded servers')
        return None


    async def send_request(self,body):
        #print('Asking server for',body)
        msg = [b'',b'MDPC01',0x01.to_bytes(1,'big')] + body
        server = body[0]
        #print(body)
        self.send_message(msg)
        answ = await self.recieve_message(server)
        #print('got an answer')

#        empty = answ.pop(0)
 #       assert empty == b''

  #      answ = pickle.loads(answ.pop(0))
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
        while True:
            try:
                #print('polling')
                items = await self.poller.poll(1000)
                if items:
                    msg = await self.socket.recv_multipart()
                    #print('recieved',msg)
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
        self.get_server_info()
        msg = ""
        lst = [getattr(self,server) for server in dir(self) if getattr(getattr(self,server),'is_remote_server',False)]
        if len(lst) == 0:
            return 'No servers connected'
        else:
            for aserver in lst:
                msg += aserver.name + "\n"
        return msg.strip()


async def main(loop):
    brokerconn = "tcp://localhost:5559"

    client  = QWeatherClient(brokerconn,loop)
    await loop.create_task(client.get_server_info())
    tic = time.time()
    loop.create_task(client.run())
    for i in range(10):
        a = loop.create_task(client.TestServer.get_number())
        b = loop.create_task(client.TestServer2.get_number())
#    loop.create_task(client.run())
 #   print("Connecting to hello world server...")
        c = await a+ await b
#        print('a: ',await a)
 #       print('b: ',await b)
    toc = time.time()
    print(toc-tic)



    #a =await client.TestServer.multiply_stuff(7,2)
#    tic = time.time()
 #   client.run()
  #  a = client.TestServer.get_number()#client.send_request([b'TestServer',b'get_number',pickle.dumps([(),{}])]))
#    b = loop.create_task(client.TestServer2.get_number())#client.send_request([b'TestServer2',b'get_number',pickle.dumps([(),{}])])
  #  print('a:', await a)
 #   print('b:', await b)
   # toc = time.time()
    #print(toc-tic)




if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))