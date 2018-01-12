from QWeatherAPI import QWeatherClient

brokerconn = "tcp://localhost:5559"
client = QWeatherClient(brokerconn)
T1 = client.TestServer

print(T1.get_number())
print(T1.get_number())