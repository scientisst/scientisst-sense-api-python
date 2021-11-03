#!/bin/python

import sys
from scientisst.scientisst import *
from threading import Timer
import sys
from argparse import ArgumentParser
from threading import Thread, Event, Lock
from queue import Queue

from pylsl import StreamInfo, StreamOutlet, local_clock


recording=False

def run_scheduled_task(scientisst,DURATION):
    timer = Timer(DURATION, stop, [scientisst])
    timer.start()

def stop(scientisst):
    global recording
    recording=False
    scientisst.stop()
    scientisst.disconnect()

def main(argv):
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
        '-s',
        '--lsl',
        dest='stream',
        action='store_true',
        default=False,
        help="stream data using Lab Streaming Layer protocol"
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

    if args.stream:
        # create LSL stream info
        info = StreamInfo("ScientISST Sense","RAW",len(args.channel),args.fs,"int32")

        lsl_buffer = Queue()
        event = Event()
        t = Thread(target=send_lsp, args=(info, lsl_buffer, event,num_frames))
        data_lock = Lock()



    scientisst.start(args.fs, args.channel, args.output, False)
    if args.stream:
        t.start()

    recording = True
    print("Start acquisition")

    stream=False
    if args.duration>0:
        run_scheduled_task(scientisst,args.duration)
    try:
        while recording:
            frames = scientisst.read(num_frames)
            if args.stream:
                with data_lock:
                    lsl_buffer.put(frames)
            if args.verbose:
                print(frames[0])
    except KeyboardInterrupt:
        pass
    print("Stop acquisition")
    if args.stream:
        event.set()
    stop(scientisst)
    sys.exit(0)

def send_lsp(info, buffer, event,num_frames):
    data_lock = Lock()
    # make outlet
    outlet = StreamOutlet(info,chunk_size=num_frames)

    timestamp = local_clock()
    previous_index = -1
    dt = 1/info.nominal_srate()
    frames = None

    print("Start LSL stream")
    while not event.is_set():
        with data_lock:
            if not buffer.empty():
                frames = buffer.get()
        if frames:
            chunk = [frame.a for frame in frames]

            current_index = frames[-1].seq
            lost_frames = current_index - ((previous_index + num_frames) & 15)

            if lost_frames>0:
                # print("Lost frames: {}".format(lost_frames))
                timestamp = local_clock()
            else:
                timestamp += num_frames * dt

            previous_index = current_index
            outlet.push_chunk(chunk, timestamp)
            frames = None
        else:
            time.sleep(0.1)

    print("Stop LSL stream")


if __name__ == "__main__":
    main(sys.argv)
