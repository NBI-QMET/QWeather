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
print('\nBroker and servers started in other threads\n')
try:
	brokerconn = "tcp://localhost:5559"	
	client = qweather.QWeatherClient(brokerconn,'testclient',debug=True,verbose=True)
		#print('listened')
	print('\nClient created\n')
	time.sleep(2)
	T1 = client.ServerA
	T2 = client.ServerB
	print("\n****Getting random numbers")
	for i in range(1):
		print('    From Server A: ',T1.get_number())
		print('    From Server B: ',T2.get_number())
	print("    Got numbers from two servers")

	print("\n****Testing crashing function on serverA")
	print("    Server responce: \"",T1.crashing_function(),'\"')
	print("    Getting random number of serverB:")
	print('    From Server B: ',T2.get_number())
	print('    Trying to get number from the crashed serverA:')
	print('    From Server A: ',T1.get_number())
	print("    Crashtest completed")

	print("\n****Testing default timeout on synchronous call")
	print("    Responce:\n    \"",T1.very_long_function(),"\"")

	print("\n****Testing setting timeout to 100 ms")
	print("    Responce:\n    \"",T1.very_long_function(qweather_timeout=100),"\"")

	print("\n****Testing setting timeout to 5000 ms")
	print("    Responce:\n    \"",T1.very_long_function(qweather_timeout=5000),"\"")




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

