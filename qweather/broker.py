"""
The message broker module of qweather, called QWeatherStation

Messages follow a modified Majo Domo pattern ( https://rfc.zeromq.org/spec/7/) called the QWeatherProtocol (QWP)

The incoming message is first sorted by who sent it (Client, Server, Ping, Pong, Execute Command)
The second stage sorts by the command (Reply,Request,Ready,Disconnect)
"""

from .constants import *
import zmq
from zmq.devices import ThreadProxy
from zmq.asyncio import Context,Poller
import asyncio
import pickle
import time
import re
import logging
#from zmq.asyncio import Context, Poller


class QWeatherStation:
    """Central broker for the communcation done in QWeather"""
    def __init__(self,IP,loop = None,verbose=False,debug = False):
        if loop is None:
            #from zmq import Context,Poller
#        import asyncio
 #       from zmq.asyncio import Context,Poller
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop

        IpAndPort = re.search(IPREPATTERN,IP)
        assert IpAndPort != None, 'Ip not understood (tcp://xxx.xxx.xxx.xxx:XXXX or txp://*:XXXX)'
        self.StationIP = IpAndPort.group(1)
        self.StationSocket = IpAndPort.group(2)
        assert self.StationIP[:6] == 'tcp://', 'Ip not understood (tcp://xxx.xxx.xxx.xxx:XXXX or txp://*:XXXX)'
        assert len(self.StationSocket) == 4, 'Port not understood (tcp://xxx.xxx.xxx.xxx:XXXX or txp://*:XXXX)'
        formatting = '{:}: %(levelname)s: %(message)s'.format('QWeatherStation')
        if debug:
            logging.basicConfig(format=formatting,level=logging.DEBUG)
        if verbose:
            logging.basicConfig(format=formatting,level=logging.INFO)
        self.servers = {} # key:value = clientaddress:value, bytes:string
        self.clients = {} # key:value = clientaddress:value, bytes:string
        self.servermethods = {}
        self.serverjobs = {}
        self.pinged = []
        self.requesttimeoutdict = {}
        self.cnx = Context()
        self.socket = self.cnx.socket(zmq.ROUTER)
        self.socket.bind(self.StationIP + ':' + self.StationSocket)
        self.proxy = ThreadProxy(zmq.XSUB,zmq.XPUB)
        self.proxy.bind_in(self.StationIP + ':' + str(int(self.StationSocket) + PUBLISHSOCKET))
        self.proxy.bind_out(self.StationIP + ':' + str(int(self.StationSocket) + SUBSOCKET))
        self.proxy.start()
        self.poller = Poller()
        self.poller.register(self.socket,zmq.POLLIN)


        logging.info('Ready to run on IP: {:}'.format(self.get_own_ip()))


    def get_own_ip(self):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    async def async_run(self):
        """Ansynchronous run the broker by polling the socket repeatedly"""
        while True:
            try:
                items = await self.poller.poll(1000)
            except KeyboardInterrupt:
                self.close()
                break

            if items:
                msg = await self.recieve_message()
                self.handle_message(msg)

          

    def run(self):
        """Runs the broker, enabling message handling (blocking if called from a scrip)"""
        self.loop.run_until_complete(self.async_run())

    def close(self):
        """Closing function, called at exit"""
        self.poller.unregister(self.socket)
        self.socket.close()

    def handle_message(self,msg):
        """The first step of message handling.\n
        First assert that the second frame is empty\n
        Then process either [S]erver, [C]lient, [P]ing [b]pong, or [#] for executing broker functions
        """
        sender = msg.pop(0)
        if sender in self.clients.keys():
            logging.debug('Recieved message from {:}:\n{:}'.format(self.clients[sender],msg,'\n\n'))    
        else:
            logging.debug('Recieved message from ID:{:}:\n{:}'.format(int.from_bytes(sender,byteorder='big'),msg,'\n\n'))
        empty = msg.pop(0)
        assert empty == b''
        SenderType = msg.pop(0)


        #Server
        if SenderType == b'S': 
            command = msg.pop(0) # 0xF? for server and 0x0? for client
            self.process_server(sender,command,msg)

        #Client
        elif (SenderType == b'C'):
            command = msg.pop(0) # 0xF? for server and 0x0? for client
            self.process_client(sender,command,msg)

        #Ping
 #       elif SenderType == b'P':
 #           if sender in self.clients.keys():
 #               logging.debug('Recieved Ping from "{:}"'.format(self.clients[sender]))
 #           else:
 #               logging.debug('Recieved Ping from ID:{:}'.format(int.from_bytes(sender,byteorder='big')))

#            self.socket.send_multipart([sender,b'',b'b']) #Sending an upside down P (b) to indicate a pong       

        #Pong
        elif SenderType ==b'b':
            logging.debug('Recieved Pong from ID:{:}'.format(int.from_bytes(sender,byteorder='big')))
            print(sender,self.pinged,sender in self.pinged)
            if sender in self.pinged:
                self.pinged.remove(sender)

        #Execute command
        elif SenderType == b'#': 
            command = msg.pop(0)
            if command == b'P': #request broker to ping all servers and remove old ones
                logging.debug('Ping of all servers requested')
                self.loop.create_task(self.ping_connections())
#            elif command == b'R': #requests the broker to "restart" by removing all connections
#                for atask in self.requesttimeoutdict.items():
#                    atask.cancel()
#                self.requesttimeoutdict = {}
#                self.servers = {}
#                self.clients = {}

            if sender in self.clients.keys():
                logging.debug('Recieved Ping from "{:}"'.format(self.clients[sender]))
            else:
                logging.debug('Recieved Ping from ID:{:}'.format(int.from_bytes(sender,byteorder='big')))

        #SenderType not understood
        else:
            logging.info('Invalid message')

    def process_client(self,sender,command,msg):
        """Second stage of the message handling. Messages go here if they came from a client"""
        if command == CREADY:
            version = msg.pop(0)
            self.handle_client_ready(sender,version,msg)

        elif command == CREQUEST:
            messageid = msg.pop(0)
            servername = msg.pop(0).decode()
            self.handle_client_request(sender,messageid,servername,msg)
            
        elif command == CDISCONNECT:
            self.handle_client_disconnect()

    def handle_client_ready(self,sender,version,msg):
        """Check the client is using the same version of QWeather, add client to clientlist and send client list of servers and servermethods"""
        if not version == PCLIENT:
            newmsg = [sender,b'',CREADY + CFAIL,'Mismatch in protocol between client and broker'.encode()]
        else:
            newmsg = [sender,b'',CREADY + CSUCCESS] + [pickle.dumps(self.servers)] + [pickle.dumps(self.servermethods)]

            name = msg.pop(0).decode()
            self.clients[sender] = name
            logging.info('Client ready at ID:{:} name:{:}'.format(int.from_bytes(sender,byteorder='big'),self.clients[sender]))
        self.send_message(newmsg)

    def handle_client_request(self,sender,messageid,servername,msg):
        """Send a client request to the correct server. Add a timeout callback in case the server response timeouts"""
        try:
            #Find the server address in the server dict based on the name {address:name}
            serveraddr = next(key for key, value in self.servers.items() if value == servername) 
            #Create a timeout call which returns an exception if the reply from the server times out.
            timeout = self.loop.call_later(B_SERVERRESPONSE_TIMEOUT, self.send_message,[sender,b'',CREQUEST + CFAIL,messageid,servername.encode(),pickle.dumps((Exception('Timeout error')))])
            #Add the timeout to a dictionary so we can find it later (and cancel it before it times out)
            self.requesttimeoutdict[messageid+sender] = timeout

            msg = [serveraddr,b'',CREQUEST,messageid,sender] + msg
            #If the joblist for the requested server is empty, send it to the server, else add it to the serverjoblist for later execution
            if len(self.serverjobs[serveraddr]) ==  0:
                self.send_message(msg)
                logging.debug('Client request from "{:}":\n{:}'.format(self.clients[sender],msg))
            else:
                self.serverjobs[serveraddr].append(msg)
        except StopIteration as e:
            logging.debug('Trying to contact a server that does not exist')

    def handle_client_disconnect(self,sender):
        """Remove the client from the client dictionary"""
        logging.debug('Client "{:}" disconnecting'.format(self.clients[sender]))
        self.clients.pop(sender)


    def process_server(self,sender,command,msg):
        """Second stage of the message handling. Messages go here if they came from a server"""
        if command == CREADY:
            version = msg.pop(0)
            self.handle_server_ready(sender,version,msg)

        elif command == CREPLY:
            messageid = msg.pop(0)
            servername = self.servers[sender]
            clientaddr = msg.pop(0)
            answ = msg.pop(0)
            self.handle_server_reply(sender,messageid,servername,clientaddr,answ)
            
        elif command == SDISCONNECT:
            self.handle_server_disconnect(sender)

    def handle_server_ready(self,sender,version,msg):
        """Check the server is using the same version of QWeather.\n
        Add the server to the serverdict, add the methods to the servermethods dict, add an empty list to the serverjobs dict\n
        Keys for all 3 dicts are the serveraddress/id assigned by ZMQ (the first frame of every message recieved)"""
        if not version == PSERVER:
            newmsg = [sender,b'',CREADY + CFAIL,'Mismatch in protocol between server and broker'.encode()]
        else:
            servername = msg.pop(0).decode()
            servermethods = pickle.loads(msg.pop(0))
            self.servers[sender] = servername
            self.servermethods[sender] = servermethods
            self.serverjobs[sender] = []
            newmsg = [sender,b'',CREADY + CSUCCESS]
            logging.info('Server "{:}" ready at: {:}'.format(servername,int.from_bytes(sender,byteorder='big')))
        self.send_message(newmsg)

    def handle_server_reply(self,sender,messageid,servername,clientaddr,answer):
        """Forward the server reply to the client that requested it.\n
        Also cancel the timeout callback now that the server has replied in time\n
        If there are more jobs in the serverjob list for this server, send the oldest one to the server"""
        msg = [clientaddr,b'',CREQUEST + CSUCCESS,messageid,servername.encode(),answer]
        try:
            #Cancel the timeout callback created when the request was sent ot the server
            timeouttask = self.requesttimeoutdict.pop(messageid+clientaddr)
            timeouttask.cancel()
            self.send_message(msg)
            logging.debug('Server answer to Client "{:}":\n{:}'.format(self.clients[clientaddr],msg))
            #If there are more requests in queue for the server, send the oldest one
            if len(self.serverjobs[sender]) > 0:
                self.send_message(self.serverjobs[sender].pop(0))
        except KeyError:
            print("Trying to send answer to client that does not exist")

    def handle_server_disconnect(self,sender):
        """Remove the server from the server, serverjobs and servermethods dictionaries"""
        logging.debug('Server  "{:}" disconnecting'.format(self.servers[sender]))
        self.servers.pop(sender)
        self.serverjobs.pop(sender)
        self.servermethods.pop(sender)



    def send_message(self,msg):
        """Send a multi-frame-message over the zmq socket"""
        self.socket.send_multipart(msg)

    async def recieve_message(self):
        """Recieve a multi-frame-message over the zmq socket (async)"""
        msg = await self.socket.recv_multipart()
        return msg

    async def ping_connections(self):
        """Ping all connections, then await 2 seconds and check if the pings responded"""
        self.__ping()
        await asyncio.sleep(2)
        self.__check_ping()

    def __ping(self):
        self.pinged = []
        for addresse in self.servers.keys():
            self.socket.send_multipart([addresse,b'',CPING,b'P'])
            self.pinged.append(addresse)

    def __check_ping(self):
        print([self.servers[i] for i in self.pinged])
        for aping in self.pinged:
            for aname,aserver in self.servers.items():
                print(self.servers[aping],aserver)
                if aping == aname:
                    logging.debug('Found a server that didnt respond to the ping. Removing: ',aserver)
                    logging.debug()
                    break
            del self.servers[aname]
        self.pinged = []

    def get_servers(self):
        """Return the server dictionary"""
        return self.servers

    def get_clients(self):
        """Return the client dictionary"""
        return self.clients