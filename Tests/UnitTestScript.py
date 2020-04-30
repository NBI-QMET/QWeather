import unittest
import sys
import time
sys.path.append('../')
import subprocess
import qweather
import asyncio
from unittest.mock import MagicMock,patch

class AsyncMoc(MagicMock):
    async def __call__(self,*args,**kwargs):
        return super().__call__(*args,**kwargs)


class ClientServerTestCases(unittest.TestCase):
    def setUp(self):
        self.procBroker = subprocess.Popen(['python','-i', 'TestBroker.py','--verbose','--debug'],creationflags=subprocess.CREATE_NEW_CONSOLE)
        time.sleep(1)
        self.procServer1 = subprocess.Popen(['python', 'TestServer.py','ServerA','--verbose','--debug'],creationflags=subprocess.CREATE_NEW_CONSOLE)
        time.sleep(1)
        self.procServer2 = subprocess.Popen(['python', 'TestServer.py','ServerB'],creationflags=subprocess.CREATE_NEW_CONSOLE)
        time.sleep(1)
        brokerconn = "tcp://localhost:5559" 
        self.client = qweather.QWeatherClient(brokerconn,'testclient',debug=True,verbose=True)


    def tearDown(self):
        self.procBroker.kill()
        self.procServer1.kill()
        self.procServer2.kill()
        self.procBroker.wait()
        self.procServer1.wait()
        self.procServer2.wait()


    def test_simple_call(self):
        self.assertEqual(self.client.ServerA.get_number(), 2,'incorrect return number')

#    @unittest.skip('lol')
    def test_crashing_call(self):
        self.assertRaises(Exception,self.client.ServerA.crashing_function())

 #   @unittest.skip('Skipping the synchronous call timeout tests')
    def test_timeout_synchronous_call(self):
        self.assertRaises(Exception,self.client.ServerA.very_long_function())
        self.assertEqual(self.client.ServerA.very_long_function(timeout=7000),2,'Timeout keyword did not work')

#    def test_connect_and_reconnect(self):
 #       self.assertEqual(self.procBroker(),['ServerA,ServerB'])
    #@unittest.skip('lol')
    def test_ServerBrokerStringRepresentationBroker_serverlist(self):
        self.assertEqual(self.client.__repr__(),'ServerA\nServerB','Broker not returning correct serverlist')
        print(self.client.ServerA.get_number)
        self.assertEqual(self.client.ServerA.__repr__(),'crashing_function\ndo_something_scheduled\nget_number\nping\nvery_long_function','Server not returning correct methodlist')
        self.assertEqual(self.client.ServerA.get_number.__doc__,'Returns the number 2',"Method not returning correct docstring")



if __name__ == '__main__':
    unittest.main()
