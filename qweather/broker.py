from .constants import *
import zmq
import pickle

class QWeatherStation:

    def __init__(self,IP,verbose=False,debug = False):
        self.StationIP = IP
        self.verbose = verbose
        self.debug = debug
        self.servers = {}
        self.clients = []
        self.workingservers = {}
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
                SenderType = msg.pop(0)
                command = msg.pop(0) # 0xFx for server and 0x0x for client
                if SenderType == b'S': #server
                    self.process_server(sender,command,msg)
                elif (SenderType == b'C'): #client
                    self.process_client(sender,command,msg)

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
            self.socket.send_multipart(newmsg)

        elif command == CREQUEST:
            server = msg.pop(0).decode()
            serveraddr = self.servers[server][0]
            msg = [serveraddr,b'',CREQUEST,sender] + msg
            print(len(self.servers[server][2]))
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
                if self.verbose:
                    print('Server "',servername,'" ready at: "',int.from_bytes(sender,byteorder='big'),'"')
            self.socket.send_multipart(newmsg)

        elif command == CREPLY:
            server = msg.pop(0).decode()
            client = msg.pop(0)
            answ = msg.pop(0)
            msg = [client,b'',CREQUEST + CSUCCESS,server.encode(),answ]
            self.socket.send_multipart(msg)
            if self.debug:
                print('DEBUG: To "',client,'"',msg)
            if len(self.servers[server][2]) > 0:
                self.socket.send_multipart(self.servers[server][2].pop(0))
                if self.debug:
                    print('DEBUG: CLient request at"',sender,'":',msg)