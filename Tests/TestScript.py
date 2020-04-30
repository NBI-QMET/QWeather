import sys
import time
sys.path.append('../')
import subprocess
import qweather
import cProfile, pstats, io
pr = cProfile.Profile()

procBroker = subprocess.Popen(['python','-i', 'TestBroker.py','--verbose','--debug'],creationflags=subprocess.CREATE_NEW_CONSOLE)
time.sleep(1)
procServer1 = subprocess.Popen(['python','-i', 'TestServer.py','ServerA','--verbose','--debug'],creationflags=subprocess.CREATE_NEW_CONSOLE)
time.sleep(1)
procServer2 = subprocess.Popen(['python', 'TestServer.py','ServerB'],creationflags=subprocess.CREATE_NEW_CONSOLE)
time.sleep(1)

def print_message(msg):
    print('msg> ', msg)
try:
	brokerconn = "tcp://localhost:5559"	
	client = qweather.QWeatherClient(brokerconn,'testclient',debug=True,verbose=True)
		#print('listened')
	print('client created')
	time.sleep(2)
	T1 = client.ServerA
	T2 = client.ServerB
	print("Getting numbers")
	for i in range(1):
		print(T1.get_number())
		print(T2.get_number())
	print("Got numbers from two servers")

	print("Testing crashing function on server")
	print(T1.crashing_function())
	print("Crashing tested")

#	print('Testing timeout on syncrhonous call')
#	print(T1.very_long_function())
#	print('Call timed out')

#	print('Testing modifying default timeout on syncrhonous call')
#	print(T1.very_long_function(timeout=7000))
#	print('Call succeded')	

	'''
	client.ping_broker()
	T1.ping()
	input('Press enter to continue')
	client.subscribe('ServerA')
	client.subscribe('ServerB')
	T1.do_something_scheduled()
	#loop = client.loop
	#loop.create_task(client.run())
	'''
	input('Press enter to stop')
except Exception as e:
	print(e)
procBroker.kill()
procServer1.kill()
procServer2.kill()
#s = io.StringIO()
#sortby = 'cumulative'
#ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
#ps.print_stats()
#print(s.getvalue())

