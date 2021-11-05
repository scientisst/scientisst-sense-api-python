#!/bin/python

import sys
from scientisst.scientisst import *
from threading import Timer
from argparse import ArgumentParser
from threading import Thread, Event
from queue import Queue

from pylsl import StreamInfo, StreamOutlet, local_clock


def run_scheduled_task(DURATION, stop_event):
    timer = Timer(DURATION, stop, [stop_event])
    timer.start()


def stop(stop_event):
    stop_event.set()


def main(argv):
    class MyParser(ArgumentParser):
        def error(self, message):
            sys.stderr.write("error: %s\n\n" % message)
            self.print_help()
            sys.exit(2)

    usage = "%(prog)s [args] address"
    description = "description: The program connects to the ScientISST Sense device and starts an acquisition, providing the option to store the received data in a .csv file."
    parser = MyParser(usage=usage, description=description)

    parser.add_argument(
        "address",
        type=str,
        help="Linux: bluetooth MAC address, Mac: serial port address, Windows: bluetooth serial COM port",
    )
    parser.add_argument(
        "-f",
        "--frequency",
        dest="fs",
        help="sampling frequency, default: 1000",
        type=int,
        default=1000,
    )
    parser.add_argument(
        "-c",
        "--channels",
        dest="channels",
        type=int,
        nargs="+",
        help='analog channels, default: "1 2 3 4 5 6"',
        default=[1, 2, 3, 4, 5, 6],
    )
    parser.add_argument(
        "-d",
        "--duration",
        dest="duration",
        help="duration in seconds, default: unlimited",
        type=int,
        default=0,
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        help="write report to output file, default: None",
        type=str,
        default=None,
    )
    parser.add_argument(
        "-s",
        "--lsl",
        dest="stream",
        action="store_true",
        default=False,
        help="stream data using Lab Streaming Layer protocol",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_false",
        dest="verbose",
        default=True,
        help="don't print ScientISST frames",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="log",
        action="store_true",
        default=False,
        help="log sent/received bytes",
    )
    args = parser.parse_args()
    args.channels = sorted(args.channels)

    scientisst = ScientISST(args.address, log=args.log)
    scientisst.version()

    if args.fs == 1:
        num_frames = 1
    else:
        num_frames = args.fs // 5

    if args.stream:
        # create LSL stream info
        info = StreamInfo(
            "ScientISST Sense",
            "RAW",
            len(args.channels),
            args.fs,
            "int32",
            args.address,
        )

        lsl_buffer = Queue()
        stream_event = Event()
        lsl_thread = Thread(
            target=__send_lsp, args=(info, lsl_buffer, stream_event, num_frames)
        )

    if args.output:
        f = __init_file(args.output, args.channels)
        file_buffer = Queue()
        file_event = Event()
        file_thread = Thread(target=__write_frames, args=(f, file_buffer, file_event))
        file_thread.start()

    stop_event = Event()

    scientisst.start(args.fs, args.channels)
    if args.stream:
        lsl_thread.start()

    print("Start acquisition")

    stream = False
    if args.duration > 0:
        run_scheduled_task(args.duration, stop_event)
    try:
        while not stop_event.is_set():
            frames = scientisst.read(num_frames)
            # print([frame.seq for frame in frames])
            if args.stream:
                lsl_buffer.put(frames)
            if args.output:
                file_buffer.put(frames)
            if args.verbose:
                print(frames[0])
    except KeyboardInterrupt:
        pass
    print("Stop acquisition")
    if args.stream:
        stream_event.set()
    if args.output:
        file_event.set()

    scientisst.stop()
    scientisst.disconnect()

    sys.exit(0)


def __send_lsp(info, buffer, event, num_frames):
    # make outlet
    outlet = StreamOutlet(info, chunk_size=num_frames)

    timestamp = local_clock()
    previous_index = -1
    dt = 1 / info.nominal_srate()
    frames = None

    print("Start LSL stream")
    while not event.is_set():
        if not buffer.empty():
            frames = buffer.get()

            chunk = [frame.a for frame in frames]

            current_index = frames[-1].seq
            lost_frames = current_index - ((previous_index + num_frames) & 15)

            if lost_frames > 0:
                # print("Lost frames: {}".format(lost_frames))
                timestamp = local_clock()
            else:
                timestamp += num_frames * dt

            previous_index = current_index
            outlet.push_chunk(chunk, timestamp)
            frames = None
        else:
            time.sleep(0.2)

    print("Stop LSL stream")


def __init_file(filename, channels):
    f = open(filename, "w")
    print("Saving data to {}".format(filename))

    header = "NSeq, I1, I2, O1, O2, "
    channel_labels = []
    for ch in channels:
        if ch == AX1 or ch == AX2:
            channel_labels += "AX{}".format(ch)
        else:
            channel_labels += "AI{}".format(ch)
    header += ", ".join(channel_labels)
    f.write(header + "\n")
    return f


def __write_frames(f, buffer, event):
    while not event.is_set():
        if not buffer.empty():
            frames = buffer.get()
            f.write("\n".join(map(str, frames)) + "\n")
        else:
            time.sleep(0.2)
    f.close()


if __name__ == "__main__":
    main(sys.argv)
