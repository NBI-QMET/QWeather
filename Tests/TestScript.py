import sys
import time
sys.path.append('../')
import subprocess
import qweather
import cProfile, pstats, io
pr = cProfile.Profile()

with subprocess.Popen(['python', 'TestBroker.py'],creationflags=subprocess.CREATE_NEW_CONSOLE) as procBroker:
	time.sleep(1)
	with subprocess.Popen(['python', 'TestServer.py 0 80 80 0'],creationflags=subprocess.CREATE_NEW_CONSOLE) as procServer1:
		time.sleep(1)
		with subprocess.Popen(['python', 'TestServer2.py'],creationflags=subprocess.CREATE_NEW_CONSOLE) as procServer2:
			time.sleep(1)

			brokerconn = "tcp://localhost:5559"	
			client = qweather.QWeatherClient(brokerconn,'testclient',debug=True,verbose=True)
			T1 = client.TestServer
			T2 = client.TestServer2
			pr.enable()
			for i in range(1):
				print(T1.get_number())
				print(T2.get_number())


			pr.disable()
			client.ping_broker()
			T1.ping()
			input('Press enter to continue')
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

