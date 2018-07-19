import sys
import time
sys.path.append('../')
import subprocess
import qweather
import cProfile, pstats, io
pr = cProfile.Profile()


procServer1 = subprocess.Popen(['python', 'TestServer.py'])
time.sleep(1)
procBroker = subprocess.Popen(['python', 'TestBroker.py'])
time.sleep(1)
procServer2 = subprocess.Popen(['python', 'TestServer2.py'])
time.sleep(5)

brokerconn = "tcp://localhost:5559"
client = qweather.QWeatherClient(brokerconn,'testclient')
T1 = client.TestServer

procBroker.kill()
time.sleep(1)
procBroker = subprocess.Popen(['python', 'TestBroker.py'])

#s = io.StringIO()
#sortby = 'cumulative'
#ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
#ps.print_stats()
#print(s.getvalue())

