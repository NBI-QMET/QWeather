"""Constants used for the servers, clients and brokers"""

PSERVER = 'QWPS02'.encode() #Server following majordomopatternv 0.2
PCLIENT = 'QWPC02'.encode() #Client following majordomopatternv 0.2
CREADY = '1'.encode()
CREQUEST = '2'.encode()
CREPLY = '3'.encode()
CDISCONNECT = '4'.encode()

SDISCONNECT = '5'.encode()

CFAIL = '00'.encode()
CSUCCESS = '11'.encode()

CPING = '99'.encode()

B_SERVERRESPONSE_TIMEOUT = 10 #timeout for the broker to recieve a reply to a request
CSYNCTIMEOUT = 5000 # timeout for synchronous client requests, in milliseconds

IPREPATTERN = ('(.*[0-9*t]):(.*[0-9])')

PUBLISHSOCKET = 2
SUBSOCKET = 1




