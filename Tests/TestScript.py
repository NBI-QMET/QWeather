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
time.sleep(1)

brokerconn = "tcp://localhost:5559"	
client = qweather.QWeatherClient(brokerconn,'testclient',debug=False)
T1 = client.TestServer
T2 = client.TestServer2
pr.enable()
for i in range(1):
	print(T1.get_number())
	print(T2.get_number())


pr.disable()
client.ping_broker()
T1.ping()

client.subscribe('TestServer')
client.subscribe('TestServer2')
T1.do_something_scheduled()
loop = client.loop
loop.create_task(client.run())
input('Press enter to stop')
procBroker.kill()
procServer1.kill()
procServer2.kill()
#s = io.StringIO()
#sortby = 'cumulative'
#ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
#ps.print_stats()
#print(s.getvalue())

