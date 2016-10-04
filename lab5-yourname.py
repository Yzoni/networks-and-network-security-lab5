## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME:
## STUDENT ID:
import Tkinter as tk
import argparse
import select
import sys
import time
from Queue import Queue
from random import randint  # Get random position in NxN grid.
from socket import *
from threading import Thread

from gui import MainWindow
from sensor import *


def random_position(n):
    x = randint(0, n)
    y = randint(0, n)
    return (x, y)


class Sensor:
    """
    Main class uses UI and Worker classes and manages their thread closing.
    Communication between threads is handled by queues
    """

    def __init__(self, mcast_addr, sensor_pos, sensor_range, sensor_val, grid_size, ping_period):
        """
        :param mcast_addr: udp multicast (ip, port) tuple.
        :param sensor_pos: (x,y) sensor position tuple.
        :param sensor_range: range of the sensor ping (radius).
        :param grid_size: length of the  of the grid (which is always square).
        :param ping_period: time in seconds between multicast pings.
        """
        self.uiprint_queue = Queue()
        self.command_queue = Queue()
        self.mcast_addr = mcast_addr
        self.sensor_pos = sensor_pos
        self.sensor_range = sensor_range
        self.sensor_val = sensor_val
        self.grid_size = grid_size
        self.ping_period = ping_period
        self.neighbours = []  # Contains ((x position, y position), (ip_address, port))

    def run(self):
        """
        Runner function
        """
        ui_thread = UI(self.uiprint_queue, self.command_queue)
        work_thread = Worker(self)
        ui_thread.start()
        work_thread.start()

        while work_thread.is_alive():
            # If the ui thread died also stop the worker thread
            # The ui thread could die from clicking on the UI stop button
            if not ui_thread.is_alive():
                work_thread.stop()
                break


class UI(Thread):
    def __init__(self, uiprint_queue, command_queue, group=None, target=None, name=None, args=(), kwargs=None,
                 verbose=None):
        self.uiprint_queue = uiprint_queue
        self.command_queue = command_queue
        self.go = True
        super(UI, self).__init__(group, target, name, args, kwargs, verbose)

    def run(self):
        w = MainWindow()
        # update() returns false when the user quits or presses escape.
        try:
            while w.update():
                # if the user entered a line getline() returns a string.
                line = w.getline()

                # Received lines
                while not self.uiprint_queue.empty():
                    timestamp = time.strftime("%d/%m/%Y %H:%M:%S")
                    w.writeln(timestamp + ' | ' + self.uiprint_queue.get())

                # Sending lines
                if line:
                    timestamp = time.strftime("%d/%m/%Y %H:%M:%S")
                    w.writeln(timestamp + ' | ' + line)
                    self.command_queue.put(line)
        except tk.TclError:
            print('GUI closed')
            return

    def stop(self):
        self.go = False


class Worker(Thread):
    def __init__(self, sensor,
                 group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        # Receive queue
        self.uiprint_queue = sensor.uiprint_queue
        self.command_queue = sensor.command_queue
        self.sensor = sensor
        self.go = True

        # Setup sockets
        self.mcast_socket = self.create_multicast_listener_socket()
        self.peer_socket = self.create_peer_socket()

        # Setup sensor message helper class
        # Key is sequence and value is the the instance
        self.message = Message()

        # Contains echoAlgo instances
        self.echoAlgo = dict()
        self.echoAlgo_sequence_nr = 0

        super(Worker, self).__init__(group, target, name, args, kwargs, verbose)

    def run(self):
        """
        Main runner function
        """
        self.init_run()
        while self.go:
            readable_sockets, writable_sockets, exception_sockets = select.select([self.mcast_socket, self.peer_socket],
                                                                                  [], [], 1)
            for r in readable_sockets:
                data, address = r.recvfrom(1024)
                if data:
                    data_decoded = self.message.message_decode(data)
                    msg_type = data_decoded[0]
                    self.handle_message(msg_type, data_decoded, address)

            if not self.command_queue.empty():
                # Handle a command received from ui
                command = self.command_queue.get()
                self.handle_command(command)

    def init_run(self):
        self.uiprint_queue.put('My location is ' + str(self.sensor.sensor_pos))

    def stop(self):
        """
        Necessary to stop the infinite loop
        """
        self.go = False

    def create_multicast_listener_socket(self):
        """
        Copy paste function creating a multicast UDP socket
        Receives multicast messages
        :return: the multicast socket
        """
        # -- Create the multicast listener socket. --
        mcast = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        # Sets the socket address as reusable so you can run multiple instances
        # of the program on the same machine at the same time.
        mcast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # Subscribe the socket to multicast messages from the given address.
        mreq = struct.pack('4sl', inet_aton(mcast_addr[0]), INADDR_ANY)
        mcast.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
        if sys.platform == 'win32':  # windows special case
            mcast.bind(('localhost', mcast_addr[1]))
        else:  # should work for everything else
            mcast.bind(self.sensor.mcast_addr)
        return mcast

    def create_peer_socket(self):
        """
        Copy paste function creating the peer UDP socket
        Sends multicast messages
        Receives unicast messages
        :return: Peer socket
        """
        # -- Create the peer-to-peer socket. --
        peer = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        # Set the socket multicast TTL so it can send multicast messages.
        peer.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 5)
        # Bind the socket to a random port.
        if sys.platform == 'win32':  # windows special case
            peer.bind(('localhost', INADDR_ANY))
        else:  # should work for everything else
            peer.bind(('', INADDR_ANY))
        return peer

    def handle_message(self, msg_type, data_decoded, address):
        if msg_type == self.message.MSG_PING:
            self.message_ping(data_decoded, address)
        elif msg_type == self.message.MSG_ECHO or msg_type == self.message.MSG_ECHO_REPLY:
            self.message_echo(data_decoded, address)
        elif msg_type == self.message.MSG_PONG:
            self.message_pong(data_decoded, address)

    def message_ping(self, data_decoded, address):
        initiator = data_decoded[2]
        # Add sensors to self.neighbour_list
        # Print some message to the UI, for example the initiating sensor
        if initiator == self.sensor.sensor_pos:
            self.uiprint_queue.put("Ping send")
        else:
            self_pos = self.sensor.sensor_pos
            is_in_range = abs(initiator[0] - self_pos[0]) <= self.sensor.sensor_range \
                          and abs(initiator[1] - self_pos[1]) <= self.sensor.sensor_range
            print(is_in_range)
            if is_in_range:
                msg = self.message.message_encode(1, 0, initiator, self_pos)
                self.peer_socket.sendto(msg, address)
                print('Received ping, sending pong to...' + str(address))
                self.uiprint_queue.put('Received ping, sending pong to...' + str(address))
            else:
                self.uiprint_queue.put("Received ping from " + str(initiator) + ", not in range")

    def message_pong(self, data_decoded, address):
        neighbour_position = data_decoded[3]
        # add to the neighbour list the position and the IP:port
        self.sensor.neighbours.append((neighbour_position, address))
        self.uiprint_queue.put('Received pong from neighbour' + str(neighbour_position))

    def message_echo(self, data_decoded, address):
        sequence_nr = data_decoded[1]
        initiator = data_decoded[2]
        sequence = (initiator, sequence_nr)

        self.uiprint_queue.put('Echo or echo reply received')

        # Spawn new echoAlgo instance if key is unknown
        if sequence not in self.echoAlgo:
            self.uiprint_queue.put('Unknown sequence number creating new echoAlgo instance')
            self.echoAlgo[sequence] = EchoAlgo(self.peer_socket, self.sensor, initiator, sequence_nr)

        # Run received message on echoAlgo instance
        self.echoAlgo[sequence].received_echo(address)

    def handle_command(self, command):
        # Do a manual ping
        if command == "ping":
            self.ping()
        if command == "echo":
            # Create a new echo instance and send echo
            self.echoAlgo_sequence_nr += 1
            sequence = (self.sensor.sensor_pos, self.echoAlgo_sequence_nr)
            self.echoAlgo[sequence] = EchoAlgo(self.peer_socket,
                                               self.sensor,
                                               self.sensor.sensor_pos,
                                               self.echoAlgo_sequence_nr)
            print('echo: new dict is ' + str(self.echoAlgo))
            self.echoAlgo[sequence].send_echo()

    def ping(self):
        msg = self.message.message_encode(self.message.MSG_PING, 0, self.sensor.sensor_pos, self.sensor.sensor_pos)
        self.peer_socket.sendto(msg, self.sensor.mcast_addr)

    def neighbour_discovery(self):
        # still think that this has to be in a subprocess and run in parallel with the main worker
        while True:
            self.sensor.neighbours = []
            self.ping()
            self.sleep(self.sensor.ping_period)


class EchoAlgo:
    def __init__(self, peer_socket, sensor, initiator, sequence_nr):
        self.message = Message()
        self.peer_socket = peer_socket
        self.uiprint_queue = sensor.uiprint_queue

        self.sequence_nr = sequence_nr
        self.initiator = initiator

        self.father = None
        self.replied_neighbours = []

        self.sensor = sensor

    def send_echo(self, echo_type=Message().MSG_ECHO, operation_type=Message().OP_NOOP):
        """
        Send ECHO or ECHO_REPLY
        :param echo_type:
        :param operation_type:
        :return:
        """
        for neighbour in self.sensor.neighbours:
            msg = self.message.message_encode(echo_type,
                                              self.sequence_nr,
                                              self.initiator,
                                              neighbour[0],
                                              operation_type)
            self.peer_socket.sendto(msg, (neighbour[1]))

    def received_echo(self, sender):
        # Only one neighbour, so only father, send ECHO REPLY
        if len(self.sensor.neighbours) == 1:
            self.uiprint_queue.put('ECHOALG: ECHO REPLY only one neighbour' + str(sender))
            self.send_echo(self.message.MSG_ECHO_REPLY)
            return

        # Received echo message for first time, set the father
        if not self.father:
            self.uiprint_queue.put('ECHOALG: Father not found setting father')
            self.father = sender

        # maybe check if items are the same?
        # if received from all neighbours send ECHO_REPLY to father
        # somehow the instance should be closed, when the wave is finished
        if len(self.sensor.neighbours) == len(self.replied_neighbours):
            self.uiprint_queue.put('ECHOALG: ECHO REPLY father, all neighbours responded')
            self.send_echo(self.message.MSG_ECHO_REPLY)
            return
        else:
            # if already received message from this sender,send ECHO_REPLY
            if sender in self.replied_neighbours:
                self.uiprint_queue.put('ECHOALG: already received from sender')
                self.send_echo(self.message.MSG_ECHO_REPLY)
            # Send ECHO to all neighbours of this sensor
            else:
                self.uiprint_queue.put('ECHOALG: send echo to neighbour')
                self.send_echo(self.message.MSG_ECHO)


# -- program entry point --
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--group', help='multicast group', default='224.1.1.1')
    p.add_argument('--port', help='multicast port', default=50000, type=int)
    p.add_argument('--pos', help='x,y sensor position', default=None)
    p.add_argument('--grid', help='size of grid', default=100, type=int)
    p.add_argument('--range', help='sensor range', default=50, type=int)
    p.add_argument('--value', help='sensor value', default=-1, type=int)
    p.add_argument('--period', help='period between autopings (0=off)',
                   default=5, type=int)
    args = p.parse_args(sys.argv[1:])
    if args.pos:
        pos = tuple(int(n) for n in args.pos.split(',')[:2])
    else:
        pos = random_position(args.grid)
    if args.value >= 0:
        value = args.value
    else:
        value = randint(0, 100)
    mcast_addr = (args.group, args.port)

    # RUN
    Sensor(mcast_addr, pos, args.range, value, args.grid, args.period).run()
