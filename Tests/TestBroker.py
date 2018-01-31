import sys
sys.path.append('../')
from qweather import QWeatherStation
#$import qweather.QWeatherStation

if __name__ == "__main__":
	broker = QWeatherStation("tcp://*:5559",loop = None,verbose=True,debug = True)
	broker.run()
