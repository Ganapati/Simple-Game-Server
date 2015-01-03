import uuid
from player import Player


class Rooms:

    def __init__(self, capacity=2):
        """
        Handle rooms and set maximum rooms capacity
        """
        self.rooms = {}
        self.players = {}
        self.room_capacity = capacity

    def register(self, addr, udp_port):
        """
        Register player
        """
        player = None
        for registered_player in self.players.values():
            if registered_player.addr == addr:
                player = registered_player
                player.udp_addr((addr[0], udp_port))
                break

        if player is None:
            player = Player(addr, udp_port)
            self.players[player.identifier] = player

        return player

    def join(self, player_identifier, room_id=None):
        """
        Add player to room
        """
        if player_identifier not in self.players:
            raise ClientNotRegistered()

        player = self.players[player_identifier]

        if room_id is None:
            room_id = self.create_room()

        if room_id in self.rooms:
            if not self.rooms[room_id].is_full():
                self.rooms[room_id].players.append(player)
                return room_id
            else:
                raise RoomFull()
        else:
            raise RoomNotFound()

    def leave(self, player_identifier, room_id):
        """
        Remove a player from a room
        """
        if player_identifier not in self.players:
            raise ClientNotRegistered()

        player = self.players[player_identifier]

        if room_id in self.rooms:
            self.rooms[room_id].leave(player)
        else:
            raise RoomNotFound()

    def create(self, room_name=None):
        """
        Create a new room
        """
        identifier = str(uuid.uuid4())
        self.rooms[identifier] = Room(identifier,
                                      self.room_capacity,
                                      room_name)
        return identifier

    def remove_empty(self):
        """
        Delete empty rooms
        """
        for room_id in self.rooms.keys():
            if self.rooms[room_id].is_empty():
                del self.rooms[room_id]

    def send(self, identifier, room_id, message, sock):
        """
        Send data to all players in room, except sender
        """
        if room_id not in self.rooms:
            raise RoomNotFound()

        room = self.rooms[room_id]
        if not room.is_in_room(identifier):
            raise NotInRoom()

        for player in room.players:
            if player.identifier != identifier:
                player.send_udp(identifier, message)

    def sendto(self, identifier, room_id, recipients, message, sock):
        """
        Send data to specific player(s)
        """
        if room_id not in self.rooms:
            raise RoomNotFound()

        room = self.rooms[room_id]
        if not room.is_in_room(identifier):
            raise NotInRoom()

        if isinstance(recipients, basestring):
            recipients = [recipients]

        for player in room.players:
            if player.identifier in recipients:
                player.send_udp(identifier, message)


class Room:

    def __init__(self, identifier, capacity, room_name):
        """
        Create a new room on server
        """
        self.capacity = capacity
        self.players = []
        self.identifier = identifier
        if room_name is not None:
            self.name = room_name
        else:
            self.name = self.identifier

    def join(self, player):
        """
        Add player to room
        """
        if not self.is_full():
            self.players.append(player)
        else:
            raise RoomFull()

    def leave(self, player):
        """
        Remove player from room
        """
        if player in self.players:
            self.players.remove(player)
        else:
            raise NotInRoom()

    def is_empty(self):
        """
        Check if room is empty or not
        """
        if len(self.players) == 0:
            return True
        else:
            return False

    def is_full(self):
        """
        Check if room is full or not
        """
        if len(self.players) == self.capacity:
            return True
        else:
            return False

    def is_in_room(self, player_identifier):
        """
        Check if player is in room
        """
        in_room = False
        for player in self.players:
            if player.identifier == player_identifier:
                in_room = True
                break
        return in_room


class RoomFull(Exception):
    pass


class RoomNotFound(Exception):
    pass


class NotInRoom(Exception):
    pass


class ClientNotRegistered(Exception):
    pass
