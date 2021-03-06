## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME:
## STUDENT ID:

import subprocess
import time


def main(nodes, r, steps):
    # Store processes.
    processes = []
    print(nodes)
    for node in range(nodes):
        # Open a process.
        p = subprocess.Popen(['python', 'lab5-yourname.py', '--sciencemode', 'True'],
                             stdout=subprocess.PIPE,
                             stdin=subprocess.PIPE)
        print(p)
        processes.append(p)

        size = 0

        size = execute_command(p, 'size', 'ECHOALG_SIZE:')
        if steps:
            if size == node:
                print('All nodes are connected. Number of nodes: ' + size)
        if size == nodes:
            min = execute_command(p, 'min', 'ECHOALG_MIN:')
            max = execute_command(p, 'max', 'ECHOALG_MAX:')
            sum = execute_command(p, 'sum', 'ECHOALG_SUM:')
            print("The minimum value is " + min)
            print("The maximum value is " + max)
            print("The sum of the values is " + sum)

def execute_command(process, command, output):
    process.stdin.write(command)
    process.stdin.flush()

    start_time = time.clock()
    while True:
        #if time.clock() - start_time > 10:
         #   return 0
        if process.stdout:
            line = process.stdout.readline()
            print(line)
            if line.split()[0] == output:
                return line.split()[1]
        else:
            return 0


if __name__ == '__main__':
    import sys, argparse

    p = argparse.ArgumentParser()
    p.add_argument('--nodes', help='number of nodes to spawn', required=True, type=int)
    p.add_argument('--range', help='sensor range', default=50, type=int)
    p.add_argument('--steps', help='output graph info every step', action="store_true")
    args = p.parse_args(sys.argv[1:])
    main(args.nodes, args.range, args.steps)
