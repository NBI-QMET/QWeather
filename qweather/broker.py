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
        if self.verbose:
            print('QWeatherStation ready to run on IP: "',self.StationIP,'"')

    async def async_run(self):
        while True:
            try:
                items = await self.poller.poll(1000)
            except KeyboardInterrupt:
                self.close()
                break

            if items:
                msg = await self.socket.recv_multipart()
                self.handle_message(msg)

          

    def run(self):
        while True:
            try:
                items = self.poller.poll(1000)
            except KeyboardInterrupt:
                self.close()
                break
            if items:
                msg = self.socket.recv_multipart()
                self.handle_message(msg)

    def close(self):
        self.poller.unregister(self.socket)
        self.socket.close()

    def handle_message(self,msg):
        sender = msg.pop(0)
        if self.debug:
            print('DEBUG: From "',sender,'": ',msg)
        empty = msg.pop(0)
        assert empty == b''
        SenderType = msg.pop(0)
        if SenderType == b'S': #server
            command = msg.pop(0) # 0xF? for server and 0x0? for client
            self.process_server(sender,command,msg)
        elif (SenderType == b'C'): #client
            command = msg.pop(0) # 0xF? for server and 0x0? for client
            self.process_client(sender,command,msg)


        elif SenderType == b'P': #Ping
            if self.debug:
                print('Recieved Ping from ',sender)
            self.socket.send_multipart([sender,b'',b'b']) #Sending an upside down P (b) to indicate a pong            

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
                newmsg = [sender,b'',CREADY + CFAIL,'Mismatch in protocol between server and broker'.encode()]
            else:
                servername = msg.pop(0).decode()
                servermethods = pickle.loads(msg.pop(0))
                self.servers[servername] = (sender,servermethods,[])
                newmsg = [sender,b'',CREADY + CSUCCESS]
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

