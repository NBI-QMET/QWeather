import sys
import time
sys.path.append('../')
import subprocess
import qweather
procBroker = subprocess.Popen(['python', 'TestBroker.py'])
time.sleep(0.1)
procServer1 = subprocess.Popen(['python', 'TestServer.py'])
time.sleep(0.1)
procServer2 = subprocess.Popen(['python', 'TestServer2.py'])
time.sleep(0.1)
brokerconn = "tcp://localhost:5559"
client = qweather.QWeatherClient(brokerconn)
T1 = client.TestServer

print(T1.get_number())
print(T1.get_number())

for aproc in [procBroker,procServer1,procServer2]:
	aproc.terminate()