import sys
import time
sys.path.append('../')
import subprocess
import qweather
import cProfile, pstats, io
pr = cProfile.Profile()


procBroker = subprocess.Popen(['python', 'TestBroker.py','--verbose','--debug'],creationflags=subprocess.CREATE_NEW_CONSOLE)
time.sleep(1)
procServer1 = subprocess.Popen(['python', 'TestServer.py','--verbose','--debug'],creationflags=subprocess.CREATE_NEW_CONSOLE)
time.sleep(1)
procServer2 = subprocess.Popen(['python', 'TestServer2.py'],creationflags=subprocess.CREATE_NEW_CONSOLE)
time.sleep(2)
brokerconn = "tcp://localhost:5559"
client = qweather.QWeatherClient(brokerconn,'testclient')
T1 = client.TestServer
client.ping_broker()
print(client)
time.sleep(2)
client.send_message([b'',b'#',b'P'])
print(client)
input('Press enter to kill')
procBroker.kill()
probServer1.kill()
probServer2.kill()
#s = io.StringIO()
#sortby = 'cumulative'
#ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
#ps.print_stats()
#print(s.getvalue())

