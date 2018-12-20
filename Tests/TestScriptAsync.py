import sys
import time
sys.path.append('../')
import subprocess
import qweather
import cProfile, pstats, io
import asyncio
pr = cProfile.Profile()


procBroker = subprocess.Popen(['python', 'TestBroker.py'])
#await loop.create_task(asyncio.sleep(0.3))
time.sleep(0.3)
procServer1 = subprocess.Popen(['python', 'TestServer.py'])
#await loop.create_task(asyncio.sleep(0.3))
time.sleep(0.3)
procServer2 = subprocess.Popen(['python', 'TestServer2.py'])
#await loop.create_task(asyncio.sleep(0.3))
time.sleep(0.3)
brokerconn = "tcp://localhost:5559"

client  = qweather.QWeatherClient(brokerconn,debug=False)
loop = client.loop
loop.create_task(client.run())

for i in range(2):
    a = loop.create_task(client.TestServer.get_number())
    b = loop.create_task(client.TestServer2.get_number())
    print('a: ',a)
    print('b: ',b)



