"""
The client class of qweather\n
This is the "user"
"""


from .constants import *
import zmq
import pickle
from zmq.asyncio import Context, Poller
import re
import asyncio
import time
import logging
import atexit
class QWeatherClient:
    """Client class for the QWeather messaging framework"""
    class serverclass:
        """Support class to represent the available servers as objects, with their exposed functions as callable attributes. The __repr__ makes it look like they are server objects"""
        def __init__(self,name,addr,methods,client):
            self.name = name
            self.addr = addr
            self.client = client
            for amethod in methods:
                setattr(self,amethod[0],self.bindingfunc(amethod[0],amethod[1]))


        def bindingfunc(self,methodname,methoddoc):
            """Ensures that "calling" the attribute of the "server"object with the name of a server function, sends a request to the server to execute that function and return the response"""
            def func(*args,**kwargs):
                timeout = kwargs.pop('qweather_timeout',CSYNCTIMEOUT) # This pops the value for timeout if it exists in kwargs, or returns the default timeout value. So this saves a line of code on logic check
                return self.client.send_request([self.name.encode(),methodname.encode(),pickle.dumps([args,kwargs])],qweather_timeout=timeout)
            func.__name__ = methodname
            func.__doc__ = methoddoc
            func.__repr__ = lambda: methoddoc
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

    def __init__(self,QWeatherStationIP,name = None,loop = None,debug=False,verbose=False):
        IpAndPort = re.search(IPREPATTERN,QWeatherStationIP)
        assert IpAndPort != None, 'Ip not understood (tcp://xxx.xxx.xxx.xxx:XXXX or txp://localhost:XXXX)'
        self.QWeatherStationIP = IpAndPort.group(1)
        self.QWeatherStationSocket = IpAndPort.group(2)
        assert self.QWeatherStationIP[:6] == 'tcp://', 'Ip not understood (tcp://xxx.xxx.xxx.xxx:XXXX or txp://localhost:XXXX)'
        assert len(self.QWeatherStationSocket) == 4, 'Port not understood (tcp://xxx.xxx.xxx.xxx:XXXX or txp://localhost:XXXX)'
        if loop is None:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop

        if name is None:
            import socket
            name = socket.gethostname()

        formatting = '{:}: %(levelname)s: %(message)s'.format(name)
        if debug:
            logging.basicConfig(format=formatting,level=logging.DEBUG)
        if verbose:
            logging.basicConfig(format=formatting,level=logging.INFO)
        self.name = name.encode()
        self.reconnect()
#        self.ping_broker()
        self.loop.run_until_complete(self.get_server_info())
        self.running = False
        self.messageid = 0
        atexit.register(self.close)


    def reconnect(self):
        '''connects or reconnects to the broker'''
        if self.poller:
            self.poller.unregister(self.socket)
        if self.socket: 
            self.socket.close()
        self.context = Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.connect(self.QWeatherStationIP + ':' + self.QWeatherStationSocket)
        self.subsocket = self.context.socket(zmq.SUB)
        self.subsocket.connect(self.QWeatherStationIP + ':' + str(int(self.QWeatherStationSocket) + SUBSOCKET))

        self.poller = Poller()
        self.poller.register(self.socket,zmq.POLLIN)
        self.poller.register(self.subsocket,zmq.POLLIN)

    def subscribe(self,servername,function):
        """Subscribe to a server with a callback function"""
        self.subsocket.setsockopt(zmq.SUBSCRIBE,servername.encode())
        self.subscribers[servername] = function

    def unsubscribe(self,servername):
        """Unsubscribe from a server"""
        self.subsocket.setsockopt(zmq.UNSUBSCRIBE,servername.encode())
        self.subscribers.pop(servername)
        
    
    async def get_server_info(self):
        """Get information about servers from the broker"""
        msg = [b'',b'C',CREADY,PCLIENT,self.name]
        self.send_message(msg)
        msg = await self.recieve_message()
        empty = msg.pop(0)
        assert empty == b''
        command = msg.pop(0)
        self.serverlist = []
        self.subscribers = {}
        if command == CREADY + CFAIL:
            raise Exception(msg.pop(0).decode())
        else:
            serverdict = pickle.loads(msg.pop(0))
            servermethoddict = pickle.loads(msg.pop(0))
            for addr,name in serverdict.items():
                methods = servermethoddict[addr]
                server = self.serverclass(name,addr,methods,self)
                server.is_remote_server = True
                setattr(self,name,server)
                self.serverlist.append(server)

    

    def send_request(self,body,qweather_timeout):
        """Send a request. If the client is running (i.e. in async mode) send an async request, else send a synchronous request\n
        Attach a messageID to each request. (0-255)"""
        self.messageid+=1
        if self.messageid > 255:
            self.messageid = 0
        if self.running:
            result =  asyncio.get_event_loop().create_task(self.async_send_request(body,self.messageid.to_bytes(1,'big')))
        else:
            result = self.sync_send_request(body,self.messageid.to_bytes(1,'big'),qweather_timeout)
        return result

    def ping_broker(self):
        """Ping the broker"""
        self.send_message([b'',b'P'])
        try:
            if len(self.loop.run_until_complete(self.poller.poll(timeout=2000))) == 0: #wait 2 seconds for a ping from the broker
                raise Exception('QWeatherStation not found')
            else:
                msg =  self.loop.run_until_complete(self.recieve_message())
                empty = msg.pop(0)
                pong = msg.pop(0)

                logging.debug('Recieved Pong: {:}'.format(pong))
                if pong != b'b':
                    raise Exception('QWeatherStation sent wrong Pong')              

        except Exception as e:
            self.poller.unregister(self.socket)
            self.socket.close()
            raise e
        

    def sync_send_request(self,body,ident,qweather_timeout):
        """Synchronously send request. Timeout with the default timeoutvalue [FINDOUTHOWTOLINKTOTHECONSTANTSPAGETOSHOWDEFAULTVALUE]"""
        msg = [b'',b'C',CREQUEST,ident]  + body
        server = body[0]
        self.send_message(msg)
        if len(self.loop.run_until_complete(self.poller.poll(timeout=qweather_timeout))) == 0:
            return Exception('Synchronous request timed out. Try adding following keyword to function call: "qweather_timeout=X" where X is the desired timeout in ms')
        else:
            msg = self.loop.run_until_complete(self.recieve_message())
            empty = msg.pop(0)
            assert empty == b''
            command = msg.pop(0)
            ident = msg.pop(0)
            server = msg.pop(0)
            answ = pickle.loads(msg[0])
            return answ
   
    async def async_send_request(self,body,ident):
        """Ansynchronously send request. No explicit timeout on the client side for this. Relies on the "servertimeout" on the broker side"""
        server = body[0]
        msg = [b'',b'C',CREQUEST,ident]  + body


        self.send_message(msg)
        answ = await self.recieve_future_message(ident+server) #Waits here until the future is set to completed
        self.futureobjectdict.pop(ident+server)
        return answ

    def send_message(self,msg):
        """Send a multi-frame-message over the ZMQ socket"""
        self.socket.send_multipart(msg)


    def recieve_future_message(self,id):
        """Create a future for the async request, add it to the dict of futures (id = messageid+server"""
        tmp = self.loop.create_future()
        self.futureobjectdict[id] = tmp
        return tmp

    async def recieve_message(self):
        """Recieve a multi-frame-message over the zmq socket"""
        msg = await self.socket.recv_multipart()
        return msg

    def handle_message(self,msg):
        """First step of handling an incoming message\n
        First asserts that the first frame is empty\n
        Then sorts the message into either request+success, request+fail or ping"""
        empty = msg.pop(0)
        assert empty == b''
        command = msg.pop(0)

        if command == CREQUEST + CSUCCESS:
            messageid = msg.pop(0)
            servername = msg.pop(0)
            msg = pickle.loads(msg[0])
            self.handle_request_success(messageid,servername,msg)

        elif command == CREQUEST + CFAIL:
            messageid = msg.pop(0)
            servername = msg.pop(0)
            self.handle_request_fail(messageid,servername)

        elif command == CPING:
            ping = msg.pop(0)
            if ping != b'P':
                raise Exception('QWeatherStation sent wrong ping')
            logging.debug('Recieved Ping from QWeatherStation')
            self.send_message([b'',b'b'])

    def handle_request_success(self,messageid,servername,msg):
        """Handle successful request by setting the result of the future (manually finishing the future)"""
        self.futureobjectdict[messageid + servername].set_result(msg)

    def handle_request_fail(self,messageid,servername):
        """Handle a failed request by setting the future to an exception"""
        self.futureobjectdict[messageid+server].set_exception(Exception(msg.pop(0)))

    def handle_broadcast(self,msg):
        """Handle a message on the broadcast socket by calling the callback function connected to the relevant server"""
        server= msg.pop(0).decode()
        msg = pickle.loads(msg.pop(0))
        self.subscribers[server](msg)

    async def run(self):
        """Asynchronously run the client by repeatedly polling the recieving socket"""
        self.running = True
        while True:
            try:
                socks = await self.poller.poll(1000)
                socks = dict(socks)
                if self.socket in socks:
                    msg = await self.recieve_message()
                    self.handle_message(msg)

                elif self.subsocket in socks:
                    msg = await self.recieve_message()
                    self.handle_broadcast(msg)

            except KeyboardInterrupt:
                self.close()
                break



    def close(self):
        """Closing function. Tells the broker that it disconnects. Is not called if the terminal is closed or the process is force-killed"""
        self.send_message([b'',b'C',CDISCONNECT])
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