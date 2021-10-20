#!/bin/python

import sys
from scientisst.scientisst import *
from threading import Timer
import sys
from argparse import ArgumentParser

recording=False

def run_scheduled_task(scientisst,DURATION):
    timer = Timer(DURATION, stop, [scientisst])
    timer.start()

def stop(scientisst):
    global recording
    recording=False
    scientisst.stop()
    scientisst.disconnect()
    sys.exit(0)

if __name__ == "__main__":

    usage = "%(prog)s [args] address"
    description = "description: The program connects to the ScientISST Sense device and starts an acquisition, providing the option to store the received data in a .csv file."
    parser = ArgumentParser(usage=usage, description=description)
    parser.add_argument(
        'address',
        type=str,
        help='Linux: bluetooth MAC address, Mac: serial port address, Windows: bluetooth serial COM port'
        )
    parser.add_argument(
        '-f',
        '--frequency',
        dest='fs',
        help='sampling frequency, default: 1000',
        type=int,
        default=1000,
        )
    parser.add_argument(
        '-c',
        '--channels',
        dest='channel',
        type=int,
        nargs='+',
        help='analog channels, default: "1 2 3 4 5 6"',
        default=[1,2,3,4,5,6],
        )
    parser.add_argument(
        '-d',
        '--duration',
        dest='duration',
        help='duration in seconds, default: unlimited',
        type=int,
        default=0,
        )
    parser.add_argument(
        '-o',
        '--output',
        dest='output',
        help='write report to output file, default: None',
        type=str,
        default=None,
        )
    parser.add_argument(
        '-q',
        '--quiet',
        action='store_false',
        dest='verbose',
        default=True,
        help="don't print ScientISST frames",
        )
    parser.add_argument(
        '-v',
        '--verbose',
        dest='log',
        action='store_true',
        default=False,
        help="log sent/received bytes",
        )
    args = parser.parse_args()

    scientisst = ScientISST(args.address,log=args.log)
    scientisst.version()

    if args.fs == 1:
        num_frames = 1
    else:
        num_frames = args.fs // 5

    scientisst.start(args.fs, args.channel, args.output, False, API_MODE_SCIENTISST)
    recording = True
    print("Start acquisition")

    if args.duration>0:
        run_scheduled_task(scientisst,args.duration)
    try:
        while recording:
            frames = scientisst.read(num_frames)
            if args.verbose:
                print(frames[0])
    except KeyboardInterrupt:
        print("Stop acquisition")
        stop(scientisst)
