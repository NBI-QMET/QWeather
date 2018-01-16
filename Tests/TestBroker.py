import sys
sys.path.append('../')
import qweather

if __name__ == "__main__":
	broker = qweather.QWeatherStation("tcp://*:5559",verbose=False,debug = False)
	broker.run()
