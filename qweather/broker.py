from .constants import QConstants
import zmq
import pickle

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