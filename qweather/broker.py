from .constants import *
import zmq
import pickle
import time
#from zmq.asyncio import Context, Poller

class QWeatherStation:

    def __init__(self,IP,loop = None,verbose=False,debug = False):
        if loop is None:
            from zmq import Context,Poller
        else:
            from zmq.asyncio import Context,Poller
        self.StationIP = IP
        self.verbose = verbose
        self.debug = debug
        self.servers = {}
        self.clients = []
        self.cnx = Context()
        self.socket = self.cnx.socket(zmq.ROUTER)
        self.poller = Poller()
        self.poller.register(self.socket,zmq.POLLIN)
        self.socket.bind(self.StationIP)
        self.heartbeatlist = {}
        self.heartbeattimeout = 30*HEARTBEATMAX
        if self.verbose:
            print('QWeatherStation ready to run on IP: "',self.StationIP,'"')

    async def async_run(self):
        tic = time.time()
        while True:
            try:
                items = await self.poller.poll(1000)
            except KeyboardInterrupt:
                break

            if items:
                msg = await self.socket.recv_multipart()
                self.handle_message(msg)

            toc = time.time()
            if toc-tic > self.heartbeattimeout:
                tic = time.time()
                for aconnection in self.heartbeatlist.items():
                    self.heartbeatlist[aconnection[0]] -= 1
                for aconnection in self.heartbeatlist.items():
                    if aconnection[1] < 1:
                        if self.debug:
                            print('Removing ',aconnection[0],' due to timeout')
                        try:
                            self.clients.remove(aconnection[0])
                        except ValueError:
                            pass
                        try:
                            self.servers.pop(aconnection[0])
                        except KeyError:
                            pass
                self.heartbeatlist = dict((k,v) for k,v in self.heartbeatlist.items() if v>0)

    def run(self):
        tic = time.time()
        while True:
            try:
                items = self.poller.poll(1000)
            except KeyboardInterrupt:
                break
            if items:
                msg = self.socket.recv_multipart()
                self.handle_message(msg)
            toc = time.time()
            if toc-tic > self.heartbeattimeout:
                tic = time.time()
                for aconnection in self.heartbeatlist.items():
                    self.heartbeatlist[aconnection[0]] -= 1
                for aconnection in self.heartbeatlist.items():
                    if aconnection[1] < 1:
                        if self.debug:
                            print('Removing ',aconnection[0],' due to timeout')
                        try:
                            self.clients.remove(aconnection[0])
                        except ValueError:
                            pass
                        try:
                            self.servers.pop(aconnection[0])
                        except KeyError:
                            pass
                self.heartbeatlist = dict((k,v) for k,v in self.heartbeatlist.items() if v>0)

        

    def handle_message(self,msg):
        sender = msg.pop(0)
        if self.debug:
            print('DEBUG: From "',sender,'": ',msg)
        empty = msg.pop(0)
        assert empty == b''
        SenderType = msg.pop(0)
        if SenderType == b'S': #server
            command = msg.pop(0) # 0xFx for server and 0x0x for client
            self.process_server(sender,command,msg)
        elif (SenderType == b'C'): #client
            command = msg.pop(0) # 0xFx for server and 0x0x for client
            self.process_client(sender,command,msg)

        elif SenderType == b'H': #heartbeat
            sender = msg.pop(0).decode()
            if self.debug:
                print('Recieved heartbeat from',sender)
            if sender in self.heartbeatlist:
                self.heartbeatlist[sender] = HEARTBEATMAX
        else:
            if self.verbose:
                print('Invalid message')

    def process_client(self,sender,command,msg):
        if command == CREADY:
            version = msg.pop(0)
            if not version == PCLIENT:
                newmsg = [sender,b'',CREADY + CFAIL,'Mismatch in protocol between client and broker'.encode()]
            else:
                newmsg = [sender,b'',CREADY + CSUCCESS] + [pickle.dumps(self.servers)]

                if self.verbose:
                    print('Client ready at "',int.from_bytes(sender,byteorder='big'),'"')
                name = msg.pop(0)
                if name.decode() not in self.clients:
                    self.clients.append(name.decode())
                self.heartbeatlist[name.decode()] =HEARTBEATMAX
            self.socket.send_multipart(newmsg)

        elif command == CREQUEST:
            messageid = msg.pop(0)
            server = msg.pop(0).decode()
            serveraddr = self.servers[server][0]
            msg = [serveraddr,b'',CREQUEST,messageid,sender] + msg
            if len(self.servers[server][2]) ==  0:
                self.socket.send_multipart(msg)
                if self.debug:
                    print('DEBUG: CLient request at"',sender,'":',msg)
            else:
                self.servers[server][2].append(msg)



    def process_server(self,sender,command,msg):
        if command == CREADY:
            version = msg.pop(0)
            if not version == PSERVER:
                print('went here')
                newmsg = [sender,b'',CREADY + CFAIL,'Mismatch in protocol between server and broker'.encode()]
            else:
                servername = msg.pop(0).decode()
                servermethods = pickle.loads(msg.pop(0))
                self.servers[servername] = (sender,servermethods,[])
                newmsg = [sender,b'',CREADY + CSUCCESS]
                self.heartbeatlist[servername] = HEARTBEATMAX
                if self.verbose:
                    print('Server "',servername,'" ready at: "',int.from_bytes(sender,byteorder='big'),'"')
            self.socket.send_multipart(newmsg)

        elif command == CREPLY:
            messageid = msg.pop(0)
            server = msg.pop(0).decode()
            client = msg.pop(0)
            answ = msg.pop(0)
            msg = [client,b'',CREQUEST + CSUCCESS,messageid,server.encode(),answ]
            self.socket.send_multipart(msg)
            if self.debug:
                print('DEBUG: To "',client,'"',msg)
            if len(self.servers[server][2]) > 0:
                self.socket.send_multipart(self.servers[server][2].pop(0))
                if self.debug:
                    print('DEBUG: CLient request at"',sender,'":',msg)

