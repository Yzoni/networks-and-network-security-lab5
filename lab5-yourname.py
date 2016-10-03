## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME:
## STUDENT ID:
import Tkinter as tk
import select
import socket
import time
from Queue import Queue  # Get random position in NxN grid.
from random import randint
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

    def __init__(self, host, port, cert_file=''):
        if cert_file:
            self.ssl = True
            self.cert_file = cert_file
        self.host = host
        self.port = port
        self.receive_queue = Queue()
        self.send_queue = Queue()

    def run(self):
        """
        Runner function
        :return:
        """
        ui_thread = UI(self.receive_queue, self.send_queue)
        work_thread = Worker(self.receive_queue, self.send_queue, self.host, self.port, self.cert_file)
        ui_thread.start()
        work_thread.start()

        while work_thread.is_alive():
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
                    w.writeln(self.uiprint_queue.get())

                # Sending lines
                if line:
                    timestamp = time.strftime("%d/%m/%Y %H:%M:%S")
                    w.writeln(timestamp + ' | You: ' + line)
                    self.command_queue.put(line)
        except tk.TclError:
            print('GUI closed')
            return

    def stop(self):
        self.go = False


class Worker(Thread):
    def __init__(self, uiprint_queue, command_queue, group=None, target=None, name=None, args=(), kwargs=None,
                 verbose=None):
        # Receive queue
        self.uiprint_queue = uiprint_queue
        self.command_queue = command_queue
        self.go = True
        super(Worker, self).__init__(group, target, name, args, kwargs, verbose)

    def run(self):

        self.echo_algo = EchoAlgo(socket)

        # -- Create the multicast listener socket. --
        mcast = socket.socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        # Sets the socket address as reusable so you can run multiple instances
        # of the program on the same machine at the same time.
        mcast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # Subscribe the socket to multicast messages from the given address.
        mreq = struct.pack('4sl', inet_aton(mcast_addr[0]), INADDR_ANY)
        mcast.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
        if sys.platform == 'win32':  # windows special case
            mcast.bind(('localhost', mcast_addr[1]))
        else:  # should work for everything else
            mcast.bind(mcast_addr)

        # -- Create the multicast listener socket. --
        mcast = socket.socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        # Sets the socket address as reusable so you can run multiple instances
        # of the program on the same machine at the same time.
        mcast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # Subscribe the socket to multicast messages from the given address.
        mreq = struct.pack('4sl', inet_aton(mcast_addr[0]), INADDR_ANY)
        mcast.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
        if sys.platform == 'win32':  # windows special case
            mcast.bind(('localhost', mcast_addr[1]))
        else:  # should work for everything else
            mcast.bind(mcast_addr)

        # -- Create the peer-to-peer socket. --
        peer = socket.socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        # Set the socket multicast TTL so it can send multicast messages.
        peer.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 5)
        # Bind the socket to a random port.
        if sys.platform == 'win32':  # windows special case
            peer.bind(('localhost', INADDR_ANY))
        else:  # should work for everything else
            peer.bind(('', INADDR_ANY))

        while self.go:
            readable_sockets, writable_sockets, exception_sockets = select.select([], [], [], 1)
            for r in readable_sockets:
                data = r.recv(1024)
                if data:
                # if data is ping then
                # elif data is echo do something else
                else:
                    # Stop working when server disconnects
                    self.uiprint_queue.put('Server disconnected')
                    return
                print('Worker received: ' + message)
                self.uiprint_queue.put(message)
            if not self.command_queue.empty():
                # SEND TO OTHER CLIENTS
                # if command is PING send ping to other clients
                # If command is ECHO send echo to other clients
                message = self.command_queue.get().encode()
                print('Worker sending: ' + message.decode())

    def stop(self):
        self.go = False


class EchoAlgo():
    def __init__(self, socket):
        pass

    def send_echo(self, neighbour_list):
        return None

    def receive_echo(self, neighbour_list):
        return None


# def main(mcast_addr, sensor_pos, sensor_range, sensor_val, grid_size, ping_period):
#     """
#     mcast_addr: udp multicast (ip, port) tuple.
#     sensor_pos: (x,y) sensor position tuple.
#     sensor_range: range of the sensor ping (radius).
#     sensor_val: sensor value.
#     grid_size: length of the  of the grid (which is always square).
#     ping_period: time in seconds between multicast pings.
#     """
#
#     # -- This is the event loop. --
#     while window.update():
#         pass


# -- program entry point --
if __name__ == '__main__':
    import sys, argparse

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
    # main(mcast_addr, pos, args.range, value, args.grid, args.period)
    Sensor(args.host, args.port, args.cert).run()  # TODO
