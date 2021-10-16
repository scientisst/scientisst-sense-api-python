#!/bin/python

import sys
from scientisst.scientisst import *
from threading import Timer
import sys
from optparse import OptionParser

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

def get_comma_separated_args(option, _, value, parser):
    setattr(parser.values, option.dest, list(map(int,value.split(','))))

if __name__ == "__main__":

    usage = "usage: %prog [options] address"
    parser = OptionParser(usage=usage)
    parser.add_option(
        '-f',
        '--frequency',
        dest='fs',
        help='sampling FREQUENCY, default: 1000',
        type='int',
        default=100,
        )
    parser.add_option(
        '-c',
        '--channels',
        dest='channels',
        help='analog CHANNELS, default: "1,2,3,4,5,6"',
        type='string',
        action='callback',
        callback=get_comma_separated_args,
        default=[1,2,3,4,5,6],
        )
    parser.add_option(
        '-d',
        '--duration',
        dest='duration',
        help='DURATION in seconds, default: unlimited',
        type='int',
        default=0,
        )
    parser.add_option(
        '-o',
        '--output',
        dest='output',
        help='write report to OUTPUT file, default: None',
        type='string',
        default=None,
        )
    parser.add_option(
        '-q',
        '--quiet',
        action='store_false',
        dest='verbose',
        default=True,
        help="don't print ScientISST frames",
        )
    (options, args) = parser.parse_args()

    if len(sys.argv)<2:
        parser.print_help()
        print("")
        parser.exit(msg="Provide an address.")

    address = sys.argv[1]
    scientisst = ScientISST(address,log=True)
    scientisst.version()

    if options.fs == 1:
        num_frames = 1
    else:
        num_frames = options.fs // 5

    scientisst.start(options.fs, options.channels, options.output, False, API_MODE_SCIENTISST)
    recording = True
    print("Start acquisition")

    if options.duration>0:
        run_scheduled_task(scientisst,options.duration)
    try:
        while recording:
            frames = scientisst.read(num_frames)
            if options.verbose:
                print(frames[0])
    except KeyboardInterrupt:
        print("Stop acquisition")
        stop(scientisst)
