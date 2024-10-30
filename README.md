# Assignment 2: 

## Part 1: The Chat Client
- To test the client, you need to run the **ws_chat_client.py** file by this command:
```python3 ws_chat_client.py <host> <port> <role> <-v> <-t time>```
- ```<host>``` could be localhost if you run the server on your local computer or owl.cs.umanitoba.ca if you want to test with the server is running on aviary machine
- ```<port>``` could be 8001 since this is the port our instructors use to run the server, if you run the server on local machine, make sure you set the port to 8001 too
- ```<role>``` could be one of ```[consumer, producer, both]```. 
    1. If you choose ```consumer```, you will expect to wait for the server to send message ```PING``` to client and client will send ```PONG``` back to server and you will see it in the terminal where the client code is running
    2. If you choose ```producer```, you will expect to see the client ask for your message in terminal while its running and after client send your message to server, you will see the server print out that ```Received message from (<host>, <port>)```. You can also send ```PING``` to server or send ```CLOSE``` to server to close the connection and the server will print out ```(<host>, <port>): Client closed the connection.``` If you leave the client with give any input message, after an amount of time, the server will send back ```(<host>, <port>): Server closed the connection``` and client will echo back and close.
    3. If you choose ```both```, you will expect to see client will ask for your message and you can also see ```PING``` messages from the server concurrently.
- ```<-v>``` for verbose, it help you to determine if you want to use ```print_above_prompt()``` function from ```consolelib.py``` file
- ```<-t time>``` for timeout, time is number of seconds that you want to wait for responses from server.


