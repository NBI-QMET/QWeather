"""Constants used for the servers, clients and brokers"""

PSERVER = 'QWPS02'.encode() #Server following majordomopatternv 0.2
PCLIENT = 'QWPC02'.encode() #Client following majordomopatternv 0.2
CREADY = '1'.encode()
CREQUEST = '2'.encode()
CREPLY = '3'.encode()
CDISCONNECT = '4'.encode()

CFAIL = '00'.encode()
CSUCCESS = '11'.encode()

CPING = '99'.encode()

CTIMEOUT = 2 # timeout for client requests, in seconds

