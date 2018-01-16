# QWeather

## Protocol
The protocol used is heavily inspired by the Majodomo protocol (insert link). But modified for this usecase
### Servers
#### On Startup
Frame | msg | Meaning
--- | --- | ---
1 | "" | empty delimiter
2 | "S1| Command indicating [S]erver command ready (startup)
3 | "QWPS01"| version control
4 | "TestServer" | Name of Server
5 | list | List of server methods arranged as a dictionary with the method name being the key and the docstring being the item
The server expects no reply on this message

### Client
#### On Startup
Frame | msg | Meaning
--- | --- | ---
1 | "" | empty delimiter
2 | "S1| Command indicating [S]erver command ready (startup)
3 | "QWPS01"| version control

The client expects a reply from the broker with all the servers and their accessible methods

