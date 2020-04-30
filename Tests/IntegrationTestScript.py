import sys
import time
sys.path.append('../')
import subprocess
import qweather
import cProfile, pstats, io
pr = cProfile.Profile()

procBroker = subprocess.Popen(['python', 'BrokerGUI.py'],creationflags=subprocess.CREATE_NEW_CONSOLE)
time.sleep(1)
procServer1 = subprocess.Popen(['python', 'TestServer.py','ServerA','--verbose','--debug'],creationflags=subprocess.CREATE_NEW_CONSOLE)
time.sleep(1)
procServer2 = subprocess.Popen(['python', 'TestServer.py','ServerB'],creationflags=subprocess.CREATE_NEW_CONSOLE)
time.sleep(1)
clientGUI = subprocess.Popen(['python', 'testgui.py'],creationflags=subprocess.CREATE_NEW_CONSOLE)
time.sleep(1)
input('Press enter to stop')
procBroker.kill()
procServer1.kill()
procServer2.kill()
clientGUI.kill()
#s = io.StringIO()
#sortby = 'cumulative'
#ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
#ps.print_stats()
#print(s.getvalue())

