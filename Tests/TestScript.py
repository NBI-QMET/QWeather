import sys
import time
sys.path.append('../')
import subprocess
import qweather
import cProfile, pstats, io
pr = cProfile.Profile()

#procBroker = subprocess.Popen(['python', 'TestBroker.py'])
#time.sleep(0.1)
procServer1 = subprocess.Popen(['python', 'TestServer.py'])
time.sleep(0.1)
procServer2 = subprocess.Popen(['python', 'TestServer2.py'])
time.sleep(1)
brokerconn = "tcp://localhost:5559"
print('got here')
client = qweather.QWeatherClient(brokerconn,'testclient')
print('got here too')
T1 = client.TestServer
pr.enable()
for i in range(10):
	print(T1.get_number())

pr.disable()

#s = io.StringIO()
#sortby = 'cumulative'
#ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
#ps.print_stats()
#print(s.getvalue())

