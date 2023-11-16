Function definitions...

getTime():
function called whenever a client or server needs a timestamp.
returns string of current time in "H:x M:y S:z" format



receive_data(clientPort,restart_event):

function called by client after registration to open a (blocking)listening socket at port (clientPort) and respond according to the "type" of message received.



if the restart_event is set, the socket will be closed and reopended with the most relevent data (updated by input_command)



input_command(client_name, restart_event):

function called by client also after registration to read in command inputs from the user and respond according to the "type" of command. 

if the restart_event is set, the function will be closed and reopended with the most relevent data (updated by receive_data)





main():
This is the main function. Depending on the mode the program is called with, it creates either a client process or a server process.

	Server:
		If the mode entered is -s, the program reads in the ServerPort parameter that was entered. (If missing ServerPort or invalid ServerPort value, prints fail message). If the port number is valid the server initializes an empty dictionary ("table") to hold new clients and update the statuses of its clients. It also creates another empty dictionary ("offline messages") to hold messages that will be saved. 
	The server then enters an infinite loop that involves opening a socket at ServerPort and blocking until a message is recieved. Once a message is recieved, a sequence of if-elifs is run, the conditional value depends on the specific "type" of the message (and only one is entered as a result) i.e 

		if package["type"]=="freg": 
			... 
		elif package["type"]=="GC":
			...

		elif package["type"]=="GC":
			...
		once a conditional is entered, it completes the associated task for the "type" of message received, then the server goes back to blocking, waiting for the next package.


	Client:
		If the mode entered is -c, the program reads in the <name> <server-ip> <server-port> and <client-port> that was entered. (If all these values are have valid types and ranges, the program creates a new socket and sends its name, client-port and IP address in one package to the server-ip and server-port entered and wait for a response. a response can be either a "confirmation" package or an "error" package. If the client receives an error package, this means an invalid name was sent to the server and the program will end. If the client receives a confirmation package,  it will also receive a copy of the servers new table including the client's own information. The client will then create a dictionary called "Info" that will store this table as well as the server information and other internal flags such as "QUIT","resend", and "active" (these will signal the internal state of the client while threading). After creating and updating Info, the client will then enter it's threading mode where it simultaneosly runs  receive_data and input_command with the shared Info table. This threading mode (and the whole process) only ends when the "QUIT" flag is raised (when a message is sent to the server but no ack received).





Packet structure

The packets sent between sockets are python dictionaries type-casted to strings then .encode()-d for transport. This made it convenient for receivers to decode the message, then evaluate the string into a variable to produce the original dictionary. These dictionaries can vary in the number of entries as well as the keys used, however, all dictionaries contain a "type" key whose value determines the amount (and keys available) of other entries in the dict.

the main packet types ( with associated keys and value-types ) received by clients are:



"table_update" contains {"table"-dict}
"msg" contains {"msg"-str}
"offline_messages" contains {"offline_messages"-list}
"GC" contains {"name"-str,"message"-str}
"ack" contains {"from"-str}
"status_check" contains {None}
"error" contains {message-str}




the main types received by server are:
"freg" contains {"message"-(str,int)}
"dereg" contains {"name"-str}
"reg" contains {"name"-str}
"GC" contains {"message"-str,"name"-str}
"to_offline" contains {"timestamp"-str, "name_to"-str, "name_from"-str}




Threading description:
The client mode uses threading once it compeletes registration.
The two threads are input_command and receive_data. Both threads share data through the clients global "info" variable. In its normal state, both threads are blocked, waiting for either a message to be received by the clientPort or for a command to be entered from stdin. 

(NOTE: Before the blocking, receive_data shares its listening socket to info["listenSocket"] for cases when input_command requires an ACK)



If a command is read first, depending on the type, the associated action in input_command will be executed as a result of if-elif statements conditional on the first argument sent in the input. If an action involves waiting for an acknowledgement, the listening Socket will be shared through the info variable i.e

( ln235: listenSocket=info['listenSocket'])

thus input_command will see if a message is recieved at the blocked-socket in receive_data. At the end of each action in input_command, restart_event.set() is called, which restarts the execution of receive_data allowing it to run with updated information stored in the info variable.


If data is received first from the clientPort, the associated action in receive_data will be executed as a result of if-elif statements conditional on the "type" sent in the package. If an action involves the state of the client (such as recieving a message during dereg), the function can check the global info variable and respond accordingly (info["active"]==True, in this case).

At the end of each action in receive_data, restart_event.set() is also called, which restarts the execution of input_command allowing it to run with updated information stored in the info variable.






Any known bugs:

after receiving a message the client's ">>>" prompt is blocked until another message is sent or a command is written.





Test Cases:
Test case 1,2,3 from PDF:

Test Case 1:

**server output**
>>> [Client table updated.]
{'x': ('x', '127.0.0.1', 3333, True)}
>>> [Client table updated.]
{'x': ('x', '127.0.0.1', 3333, True), 'y': ('y', '127.0.0.1', 1111, True)}
>>> [Client table updated.]
{'x': ('x', '127.0.0.1', 3333, True), 'y': ('y', '127.0.0.1', 1111, True), 'z': ('z', '127.0.0.1', 1122, True)}
>>> [Client table updated.]
{'x': ('x', '127.0.0.1', 3333, False), 'y': ('y', '127.0.0.1', 1111, True), 'z': ('z', '127.0.0.1', 1122, True)}
>>> [Client table updated.]
{'x': ('x', '127.0.0.1', 3333, True), 'y': ('y', '127.0.0.1', 1111, True), 'z': ('z', '127.0.0.1', 1122, True)}






**x output**
>>> [Welcome, You are registered.]
>>> send y hi y from x
>>> [Message received by y.]
>>> z: hi x from z
send z hi z from x
>>> [Message received by z.]
>>> y: hi x from y
dereg
>>> [You are Offline. Bye.]
>>> reg
>>> [RegSent]
>>> >>> [You have offline messages:]
>>> y: 23:32:21 hi offline x
>>> z: 23:32:35 hi offline x from z

**y output**
>>> [Welcome, You are registered.]
>>> x: hi y from x
send z hi z from y
>>> [Message received by z.]
>>> send x hi x from y
>>> [Message received by x.]
>>> z: hi y from z
send x hi offline x
>>> [Offline Message sent at 23:32:21 received by the server and saved.]
>>>  [Offline Message sent at 23:32:21 received by x.]







**z output**
>>> [Welcome, You are registered.]
>>> y: hi z from y
send x hi x from z
>>> [Message received by x.]
>>> x: hi z from x
send y hi y from z
>>> [Message received by y.]
>>> send x hi offline x from z
>>> [Offline Message sent at 23:32:35 received by the server and saved.]
>>>  [Offline Message sent at 23:32:35 received by x.]







Test Case 2:


**server pre-exit**
>>> [Client table updated.]
{'x': ('x', '127.0.0.1', 3333, True)}
>>> [Client table updated.]
{'x': ('x', '127.0.0.1', 3333, True), 'y': ('y', '127.0.0.1', 1111, True)}
>>> [Client table updated.]
{'x': ('x', '127.0.0.1', 3333, True), 'y': ('y', '127.0.0.1', 1111, True), 'z': ('z', '127.0.0.1', 1122, True)}

**x output**
>>> [Welcome, You are registered.]
>>> send z this is a discrete message
>>> [Message received by z.]
>>>


**y output**
>>> [Welcome, You are registered.]
>>> dereg
>>> [Server not responding]
>>> [Exiting]


**z output**

>>> [Welcome, You are registered.]
>>> x: this is a discrete message





Test Case 3:



**server output**
>>> [Client table updated.]
{'x': ('x', '127.0.0.1', 3333, True)}
>>> [Client table updated.]
{'x': ('x', '127.0.0.1', 3333, True), 'y': ('y', '127.0.0.1', 1111, True)}
>>> [Client table updated.]
{'x': ('x', '127.0.0.1', 3333, True), 'y': ('y', '127.0.0.1', 1111, True), 'z': ('z', '127.0.0.1', 1122, True)}
>>> [Client table updated.]
{'x': ('x', '127.0.0.1', 3333, True), 'y': ('y', '127.0.0.1', 1111, True), 'z': ('z', '127.0.0.1', 1122, True), 'a': ('a', '127.0.0.1', 1133, True)}
>>> [Client table updated.]
{'x': ('x', '127.0.0.1', 3333, True), 'y': ('y', '127.0.0.1', 1111, True), 'z': ('z', '127.0.0.1', 1122, True), 'a': ('a', '127.0.0.1', 1133, False)}
>>> [Client table updated.]
{'x': ('x', '127.0.0.1', 3333, True), 'y': ('y', '127.0.0.1', 1111, True), 'z': ('z', '127.0.0.1', 1122, True), 'a': ('a', '127.0.0.1', 1133, True)}





**x output**
>>> [Welcome, You are registered.]
>>> send_all yoyoyo everyone
>>> [Group Message received by Server.]
>>>


**y output**
>>> [Welcome, You are registered.]
>>> >>> Group Chat x:  yoyoyo everyone
send a did u see that?
>>> [Offline Message sent at 23:39:52 received by the server and saved.]
>>>  [Offline Message sent at 23:39:52 received by a.]




**z output**
>>> [Welcome, You are registered.]
>>> >>> Group Chat x:  yoyoyo everyone


**a output**
>>> [Welcome, You are registered.]
>>> dereg
>>> [You are Offline. Bye.]
>>> reg
>>> [RegSent]
>>> >>> [You have offline messages:]
>>> Group Chat x: 23:39:33 yoyoyo everyone
>>> y: 23:39:52 did u see that?






Test Case 4:
start server
start client foo 
start client bar

dereg bar
chat foo -> bar (message received by server)
dereg foo

start client baz
baz send_all 


reg bar (offline message received from foo)
reg foo (offline message received from server "offline message received by foo")

**server output**
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, True)}
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, True), 'bar': ('bar', '127.0.0.1', 2222, True)}
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, True), 'bar': ('bar', '127.0.0.1', 2222, False)}
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, False), 'bar': ('bar', '127.0.0.1', 2222, False)}
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, False), 'bar': ('bar', '127.0.0.1', 2222, False), 'baz': ('baz', '127.0.0.1', 1111, True)}
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, False), 'bar': ('bar', '127.0.0.1', 2222, True), 'baz': ('baz', '127.0.0.1', 1111, True)}
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, True), 'bar': ('bar', '127.0.0.1', 2222, True), 'baz': ('baz', '127.0.0.1', 1111, True)}



**foo output**
>>> [Welcome, You are registered.]
>>> send bar hi
>>> [Offline Message sent at 22:55:29 received by the server and saved.]
>>> dereg
>>> [You are Offline. Bye.]
>>> reg
>>> [RegSent]
>>> >>> [You have offline messages:]
>>> Group Chat baz: 22:56:40 hi everyone
>>>  [Offline Message sent at 22:55:29 received by bar.]




**bar output**

>>> [Welcome, You are registered.]
>>> dereg
>>> [You are Offline. Bye.]
>>> reg
>>> [RegSent]
>>> >>> [You have offline messages:]
>>> foo: 22:55:29 hi
>>> Group Chat baz: 22:56:40 hi everyone





**baz output**
>>> [Welcome, You are registered.]
>>> send_all hi everyone
>>> [Group Message received by Server.]
>>>




Test Case 5:
start server
start client foo 
start client bar
start client baz

foo send_all 
bar send_all 
baz send_all 

server exit
chat bar->foo
chat bar->baz
chat foo-> bar 


baz send_all (Server Not responding, Exit)

chat bar-> foo

chat bar-> baz (Server Not responding, Exit)
chat foo -> bar (Server Not responding, Exit)

**server pre-exit output**
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, True)}
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, True), 'bar': ('bar', '127.0.0.1', 2222, True)}
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, True), 'bar': ('bar', '127.0.0.1', 2222, True), 'baz': ('baz', '127.0.0.1', 1111, True)}





**foo output**
>>> [Welcome, You are registered.]
>>> send_all hi from foooo
>>> [Group Message received by Server.]
>>> >>> Group Chat bar:  hi from barrrrr
>>> Group Chat baz:  hi from bazzzzz
bar: hi foo priv
send bar whats up
>>> [Message received by bar.]
>>> bar: i think baz died
send bar no way!
>>> [No ACK from bar, message sent to server.]
>>> [Server not responding]
>>> [Exiting]






**bar output**
>>> [Welcome, You are registered.]
>>> >>> Group Chat foo:  hi from foooo
send_all hi from barrrrr
>>> [Group Message received by Server.]
>>> >>> Group Chat baz:  hi from bazzzzz
send foo hi foo priv
>>> [Message received by foo.]
>>> send baz hi baz priv
>>> [Message received by baz.]
>>> foo: whats up
send foo i think baz died
>>> [Message received by foo.]
>>> send baz yo u alive?
>>> [No ACK from baz, message sent to server.]
>>> [Server not responding]
>>> [Exiting]


**baz output**
>>> [Welcome, You are registered.]
>>> >>> Group Chat foo:  hi from foooo
>>> Group Chat bar:  hi from barrrrr
send_all hi from bazzzzz
>>> [Group Message received by Server.]
>>> bar: hi baz priv
send_all are you talking without me smfh
>>> [Server not responding]
>>> [Exiting]






Test Case 6:
start server
start client foo 
start client bar
start client baz


foo dereg
baz send_all (offline saved for foo)
baz silent-leaves
chat bar -> foo
bar send_all (server sees baz unresponsive, updates table)
 
foo reg (offline_messages: GC message from baz, message from bar, GC message from bar)
server send baz reciept (no response, rebroadcast tables)


**server output**
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, True)}
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, True), 'bar': ('bar', '127.0.0.1', 2222, True)}
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, True), 'bar': ('bar', '127.0.0.1', 2222, True), 'baz': ('baz', '127.0.0.1', 1111, True)}
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, False), 'bar': ('bar', '127.0.0.1', 2222, True), 'baz': ('baz', '127.0.0.1', 1111, True)}
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, False), 'bar': ('bar', '127.0.0.1', 2222, True), 'baz': ('baz', '127.0.0.1', 1111, False)}
>>> [Client table updated.]
{'foo': ('foo', '127.0.0.1', 3333, True), 'bar': ('bar', '127.0.0.1', 2222, True), 'baz': ('baz', '127.0.0.1', 1111, False)}



**foo output**
>>> [Welcome, You are registered.]
>>> dereg
>>> [You are Offline. Bye.]
>>> reg
>>> [RegSent]
>>> >>> [You have offline messages:]
>>> Group Chat baz: 23:10:43 Goodbye Everyone.
>>> bar: 23:11:32 yo when you see this, i think baz died again
>>> Group Chat bar: 23:11:59 baz if u can hear us, come back

**bar output**
>>> [Welcome, You are registered.]
>>> >>> Group Chat baz:  Goodbye Everyone.
send foo yo when you see this, i think baz died again
>>> [Offline Message sent at 23:11:32 received by the server and saved.]
>>> send_all baz if u can hear us, come back
>>> [Group Message received by Server.]
>>>  [Offline Message sent at 23:11:32 received by foo.]




**baz output pre-exit**
>>> [Welcome, You are registered.]
>>> send_all Goodbye Everyone.
>>> [Group Message received by Server.]
>>>






Test Case 7:

start server
start client foo 
start client bar

foo silent-leaves
bar silent-leaves

start client baz

baz send_all
baz dereg

start client wag 
chat wag -> baz
wag silent-leaves

baz reg



**server output**

**foo output pre-exit**
>>> [Welcome, You are registered.]
>>>

**bar output pre-exit**
>>> [Welcome, You are registered.]
>>>


**baz output**
>>> [Welcome, You are registered.]
>>> send_all yo anyone here
>>> [Group Message received by Server.]
>>> dereg
>>> [You are Offline. Bye.]
>>> reg
>>> [RegSent]
>>> >>> [You have offline messages:]
>>> wag: 23:28:10 i just joined what up



**wag output pre-exit**
>>> [Welcome, You are registered.]
>>> send baz i just joined what up
>>> [Offline Message sent at 23:28:10 received by the server and saved.]
>>>













