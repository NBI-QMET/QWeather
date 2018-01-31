"""Constants used for the servers, clients and brokers"""

PSERVER = 'QWPS01'.encode() #Server following majordomopatternv 0.1
PCLIENT = 'QWPC01'.encode() #Client following majordomopatternv 0.1
CREADY = '1'.encode()
CREQUEST = '2'.encode()
CREPLY = '3'.encode()
CDISCONNECT = '4'.encode()

CFAIL = '00'.encode()
CSUCCESS = '11'.encode()

