import sys
import time
sys.path.append('../')
import subprocess
import qweather
import cProfile, pstats, io
import numpy as np
pr = cProfile.Profile()

with subprocess.Popen(['python', 'TestBroker.py'],creationflags=subprocess.CREATE_NEW_CONSOLE) as procBroker:
	time.sleep(1)
	with subprocess.Popen(['python', 'TestServer.py',],creationflags=subprocess.CREATE_NEW_CONSOLE) as procServer1:
		time.sleep(1)

		brokerconn = "tcp://localhost:5559"	
		client = qweather.QWeatherClient(brokerconn,'testclient',debug=True,verbose=True)
		T1 = client.TestServer
		seed = 1234
		np.random.seed(1234)
		for i in range(1000,1001):
			try:
				testsize = int(i*1e6)
#				checknum = np.random.randn(testsize)
				testnum = T1.get_alot_of_numbers(testsize,seed)
				print('Got {:e}'.format(len(testnum)))
				time.sleep(1)
			except Exception as e:
				print(e)
				print(testnum)
				print('Failed at {:e} length of array'.format(testsize))
		print('Test over, all done!')
		procBroker.kill()
		procServer1.kill()
		
