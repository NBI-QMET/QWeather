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
brokerconn = "tcp://localhost:5559"
client = qweather.QWeatherClient(brokerconn,'testclient')
print('\nClient created\n')
print('\n****Testing available servers:')
print('    Servers available:\n',client)
print('\n****Testing killing a server and then pinging:')
print('    Killing Server A')
procServer1.kill()
print('    Servers available:\n',client)
print('    Asking broker to ping')
client.send_message([b'',b'#',b'P'])
time.sleep(5)
print('    Servers available:\n',client)
print(client.ServerA.get_number())
input('Press enter to stop')
procBroker.kill()
#probServer1.kill()
procServer2.kill()
#s = io.StringIO()
#sortby = 'cumulative'
#ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
#ps.print_stats()
#print(s.getvalue())

