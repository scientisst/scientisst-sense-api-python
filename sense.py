#!/usr/bin/python

"""
sense.py
"""

VERSION = "0.0.3"

import sys
from scientisst import *
from threading import Timer
from threading import Event
from sense.arg_parser import ArgParser
from sense.device_picker import DevicePicker
from sense.file_writer import *


def main():

    arg_parser = ArgParser()
    args = arg_parser.args

    if args.version:
        sys.stdout.write("sense.py version {}\n".format(VERSION))
        sys.exit(0)

    if args.address:
        address = args.address
    else:
        address = DevicePicker().select_device()
        if not address:
            arg_parser.error("No paired device found")

    args.channels = sorted(map(int, args.channels.split(",")))

    scientisst = ScientISST(address, log=args.log)

    if args.fs <= 5:
        num_frames = 1
    else:
        num_frames = args.fs // 5

    if args.stream:
        from sense.stream_lsl import StreamLSL

        lsl = StreamLSL(
            args.channels,
            args.fs,
            address,
            num_frames,
        )

    if args.output:
        file_writer = FileWriter(
            args.output, address, args.fs, args.channels, args.convert
        )

    stop_event = Event()

    scientisst.start(args.fs, args.channels)
    if args.stream:
        lsl.start()
    if args.output:
        file_writer.start()

    sys.stdout.write("Start acquisition\n")

    if args.duration > 0:
        run_scheduled_task(args.duration, stop_event)
    try:
        if args.verbose:
            header = "\t".join(get_header(args.channels, args.convert)) + "\n"
            sys.stdout.write(header)
        while not stop_event.is_set():
            frames = scientisst.read(num_frames, convert=args.convert)
            if args.stream:
                lsl.put(frames)
            if args.output:
                file_writer.put(frames)
            if args.verbose:
                sys.stdout.write("{}\n".format(frames[0]))
    except KeyboardInterrupt:
        pass
    sys.stdout.write("Stop acquisition\n")
    if args.stream:
        lsl.stop()
    if args.output:
        file_writer.stop()

    scientisst.stop()
    scientisst.disconnect()

    sys.exit(0)


def run_scheduled_task(DURATION, stop_event):
    def stop(stop_event):
        stop_event.set()

    timer = Timer(DURATION, stop, [stop_event])
    timer.start()


if __name__ == "__main__":
    main()
