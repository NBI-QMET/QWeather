import sys
import time
sys.path.append('../')
import subprocess
import qweather
import cProfile, pstats, io
pr = cProfile.Profile()
def print_message(msg):
	print('msg>',msg)

with subprocess.Popen(['python', 'TestBroker.py','--verbose','--debug'],creationflags=subprocess.CREATE_NEW_CONSOLE) as procBroker:
	time.sleep(1)
	with subprocess.Popen(['python', 'TestServer.py','--verbose','--debug'],creationflags=subprocess.CREATE_NEW_CONSOLE) as procServer1:
		time.sleep(1)

		brokerconn = "tcp://localhost:5559"	
		client = qweather.QWeatherClient(brokerconn,'testclient',debug=True,verbose=True)
		T1 = client.TestServer
		client.subscribe('TestServer',print_message)
		T1.do_something_scheduled()
		input('Press enter to continue')
		T1.do_something_scheduled(1)
		loop = client.loop
		loop.create_task(client.run())
		input('Press enter to stop')
		procBroker.kill()
		procServer1.kill()
		#s = io.StringIO()
		#sortby = 'cumulative'
		#ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
		#ps.print_stats()
		#print(s.getvalue())



