# QWeather

## Protocol
The protocol used is heavily inspired by the Majodomo protocol (insert link). But modified for this usecase
### Servers
#### Reply to Request
Frame | msg | Meaning
--- | :---: | ---
1 | "" | empty delimiter
2 | "S3| Command indicating [S]erver command ready (startup)
3 | "TestServer" | Name of Server
4 | "11231321" | Client addresse (not IP but socket addresse)
5 | answer | return from the method requested to being called

#### On Startup
Frame | msg | Meaning
--- | :---: | ---
1 | "" | empty delimiter
2 | "S1| Command indicating [S]erver command ready (startup)
3 | "QWPS01"| version control
4 | "TestServer" | Name of Server
5 | list | List of server methods arranged as a dictionary with the method name being the key and the docstring being the item


### Client
#### Request to server
Frame | msg | Meaning
--- | :---: | ---
1 | "" | empty delimiter
2 | "C2| Command indicating [S]erver command ready (startup)
3 | "TestServer" | Name of Server
4 | "TestMethod" | Name of Method to be called on server
5 | arguments | arguments and keyword arguments to be used in the method call on the server

#### On Startup
Frame | msg | Meaning
--- | :---: | ---
1 | "" | empty delimiter
2 | "S1| Command indicating [S]erver command ready (startup)
3 | "QWPS01"| version control

The client expects a reply from the broker with all the servers and their accessible methods

