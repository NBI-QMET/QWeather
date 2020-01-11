import sys
sys.path.append('../')
from qweather import QWeatherStation
#$import qweather.QWeatherStation

if __name__ == "__main__":
	import argparse
	my_parser = argparse.ArgumentParser()
	my_parser.add_argument('--verbose', action='store_true')
	my_parser.add_argument('--debug', action='store_true')

	args = vars(my_parser.parse_args())
	broker = QWeatherStation("tcp://*:5559",loop = None,verbose=args['verbose'],debug = args['debug'])
	broker.run()
