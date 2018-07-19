import sys
import time
sys.path.append('../')
import subprocess
import qweather
import cProfile, pstats, io
pr = cProfile.Profile()

procBroker = subprocess.Popen(['python', 'TestBroker.py'])
time.sleep(1)
procServer1 = subprocess.Popen(['python', 'TestServer.py'])
time.sleep(1)
procServer2 = subprocess.Popen(['python', 'TestServer2.py'])
time.sleep(2)

brokerconn = "tcp://localhost:5559"
client = qweather.QWeatherClient(brokerconn,'testclient')
T1 = client.TestServer
T2 = client.TestServer2
tic = time.time()
T1.long_operation(2,wait=False)
T2.long_operation(3,wait=True)
print('took: ',time.time()-tic,'s to complete')



#s = io.StringIO()
#sortby = 'cumulative'
#ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
#ps.print_stats()
#print(s.getvalue())

