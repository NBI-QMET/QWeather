from QWeatherAPI import QWeatherStation

if __name__ == "__main__":
	broker = QWeatherStation("tcp://*:5559",verbose=True,debug = False)
	broker.run()
