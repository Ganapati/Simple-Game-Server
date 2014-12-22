#!/usr/bin/python

import argparse
import socket
import json
import time
from threading import Thread, Lock
from rooms import Rooms, RoomNotFound, NotInRoom, RoomFull


def main_loop(tcp_port, udp_port, rooms):
    lock = Lock()
    udp_server = UdpServer(udp_port, rooms, lock)
    tcp_server = TcpServer(tcp_port, rooms, lock)
    udp_server.start()
    tcp_server.start()


class UdpServer(Thread):
    def __init__(self, udp_port, rooms, lock):
        Thread.__init__(self)
        self.rooms = rooms
        self.lock = lock
        self.udp_port = int(udp_port)
        self.msg = '{"success": %(success)s, "message":"%(message)s"}'

    def run(self):
        sock = socket.socket(socket.AF_INET,
                             socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", self.udp_port))
        while True:
            data, addr = sock.recvfrom(1024)
            try:
                data = json.loads(data)
                try:
                    identifier = data['identifier']
                except KeyError:
                    identifier = None

                try:
                    room_id = data['room_id']
                except KeyError:
                    room_id = None

                try:
                    payload = data['payload']
                except KeyError:
                    payload = None

                try:
                    if room_id not in self.rooms.rooms.keys():
                        raise RoomNotFound
                    self.lock.acquire()
                    try:
                        self.rooms.broadcast(identifier,
                                             room_id,
                                             payload,
                                             sock)
                    finally:
                        self.lock.release()
                except RoomNotFound:
                    print "Room not found"

            except KeyError:
                print "Json from %s:%s is not valid" % addr
            except ValueError:
                print "Message from %s:%s is not a valid json string" % addr

    def stop(self):
        pass


class TcpServer(Thread):
    def __init__(self, tcp_port, rooms, lock):
        Thread.__init__(self)
        self.lock = lock
        self.tcp_port = int(tcp_port)
        self.rooms = rooms
        self.msg = '{"success": "%(success)s", "message":"%(message)s"}'

    def run(self):
        sock = socket.socket(socket.AF_INET,
                             socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', self.tcp_port))
        time_reference = time.time()
        sock.listen(1)

        while True:

            #  Clean empty rooms
            if time_reference + 60 < time.time():
                self.rooms.remove_empty()
                time_reference = time.time()

            conn, addr = sock.accept()
            data = conn.recv(1024)
            try:
                data = json.loads(data)
                action = data['action']
                identifier = None
                try:
                    identifier = data['identifier']
                except KeyError:
                    pass  # Silently pass

                room_id = None
                try:
                    room_id = data['room_id']
                except KeyError:
                    pass  # Silently pass

                payload = None
                try:
                    payload = data['payload']
                except KeyError:
                    pass  # Silently pass
                self.lock.acquire()
                try:
                    self.route(conn,
                               addr,
                               action,
                               payload,
                               identifier,
                               room_id)
                finally:
                    self.lock.release()
            except KeyError:
                print "Json from %s:%s is not valid" % addr
                conn.send("Json is not valid")
            except ValueError:
                print "Message from %s:%s is not a valid json string" % addr
                conn.send("Message is not a valid json string")

            conn.close()

    def route(self,
              sock,
              addr,
              action,
              payload,
              identifier=None,
              room_id=None):

        if action == "register":
            client = self.rooms.register(addr, int(payload))
            client.send_tcp(True, client.identifier, sock)
            return 0

        if identifier is not None:
            if identifier not in self.rooms.players.keys():
                print "Unknown identifier %s for %s:%s" % (identifier,
                                                           addr[0],
                                                           addr[1])
                sock.send(self.msg % {"success": "False",
                                      "message": "Unknown identifier"})
                return 0

            # Get client object
            client = self.rooms.players[identifier]

            if action == "join":
                try:
                    if payload not in self.rooms.rooms.keys():
                        raise RoomNotFound()
                    self.rooms.join(identifier, payload)
                    client.send_tcp(True, payload, sock)
                except RoomNotFound:
                    client.send_tcp(False, room_id, sock)
                except RoomFull:
                    client.send_tcp(False, room_id, sock)
            elif action == "autojoin":
                room_id = self.rooms.join(identifier)
                client.send_tcp(True, room_id, sock)
            elif action == "get_rooms":
                rooms = []
                for id_room, room in self.rooms.rooms.items():
                    rooms.append({"id": id_room,
                                  "nb_players": len(room.players),
                                  "capacity": room.capacity})
                client.send_tcp(True, rooms, sock)
            elif action == "create":
                room_identifier = self.rooms.create()
                self.rooms.join(client.identifier, room_identifier)
                client.send_tcp(True, room_identifier, sock)
            elif action == 'leave':
                try:
                    if room_id not in self.rooms.rooms:
                        raise RoomNotFound()
                    rooms.leave(identifier, room_id)
                    client.send_tcp(True, room_id, sock)
                except RoomNotFound:
                    client.send_tcp(False, room_id, sock)
                except NotInRoom:
                    client.send_tcp(False, room_id, sock)
            else:
                sock.send_tcp(self.msg % {"success": "False",
                                          "message": "You must register"})

    def stop(self):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simple game server')
    parser.add_argument('--tcpport',
                        dest='tcp_port',
                        help='Listening tcp port',
                        default="1234")
    parser.add_argument('--udpport',
                        dest='udp_port',
                        help='Listening udp port',
                        default="1234")
    parser.add_argument('--capacity',
                        dest='room_capacity',
                        help='Max players per room',
                        default="2")

    args = parser.parse_args()
    rooms = Rooms(int(args.room_capacity))
    main_loop(args.tcp_port, args.udp_port, rooms)
