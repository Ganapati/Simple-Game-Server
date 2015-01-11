Simple-Game-Server
==================
A very simple client/server library for multiplayer python games
 - Handle multi-rooms
 - TCP for server actions
   - Register to server (get uniq identifier)
   - Create/join/leave room
   - List rooms and capacity (ex: room1 2/10 players)
   - Autojoin the first non-full room
 - UDP for broadcasting data to other players

Quickstart and demo
-------------------
Launch server.py on your server :
 - ./python server.py --tcpport 1234 --udpport 1234 --capacity 3
   - --udpport udp port to listen
   - --tcpport tcp port to listen
   - --capacity maximum players per room

Launch client.py :
 - the main method from client is a test-case with 3 clients instances. The first create a room, second and third join and start sending data.

How to add multiplayer in your games
------------------------------------
Start server :

```python
user@server >>> ./python server.py --tcpport 1234 --udpport 1234 --capacity 10
```

In the client code :

Only add the client.py file to your project

```python
# Add Client instance to your game
client = Client("127.0.0.1", 1234, 1234, 1235)

# Get room list (room_id, nb_players, capacity)
rooms = client.get_rooms()

# You can join a room using room identifier (ex: first room)
client.join(rooms[0]["id"])

# You can autojoin the first available room client.autojoin()
# Or you can create a new room with client.create_room("room_name")

# In your game main loop
while game_is_running:
    # Data to send
    data = {"foo": "bar", "baz": "gu"}

    # Send data to all players in the room
    client.send(data)
  
    # Send data to one player in the room
    client.sendto(someone.identifier, data)

    # Send data to multiple players in room
    players_ids = [player1.identifier, player2.identifier]
    client.sendto(players_ids, data)

    # Read received messages
    messages = client.get_messages()
    if len(messages) != 0:
        for message in message:
            do_something_with_message(message)
```
Each received message is given with remote player identifier.

Server commands
---------------

 * list : list server rooms
 * room #id : show informations about room
 * user #id : show informations about player
 * quit : quit server
