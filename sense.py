#!/usr/bin/python

"""
sense.py
"""

VERSION = "0.0.2"

import sys
from scientisst import *
from threading import Timer
from argparse import ArgumentParser
from threading import Thread, Event
from queue import Queue


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
        nargs="?",
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
        type=str,
        help="analog channels, default: 1,2,3,4,5,6",
        default="1,2,3,4,5,6",
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
        "--version",
        dest="version",
        action="store_true",
        default=False,
        help="show sense.py version",
    )
    parser.add_argument(
        "--verbose",
        dest="log",
        action="store_true",
        default=False,
        help="log sent/received bytes",
    )
    args = parser.parse_args()

    if args.version:
        sys.stdout.write("sense.py version {}\n".format(VERSION))
        sys.exit(0)

    if args.address:
        address = args.address
    else:
        options, labels = __get_device_options()
        if len(options) > 0:
            sys.stdout.write("ScientISST devices:\n")
            label_index = 1
            for label in labels:
                sys.stdout.write("[{}] {}\n".format(label_index, label))
                label_index += 1
            selected_index = 0
            while selected_index == 0:
                user_input = input("Connect to: ")
                try:
                    selected_index = int(user_input)
                    if selected_index > len(options):
                        selected_index = 0
                        raise ValueError()
                except ValueError:
                    sys.stderr.write('"{}" is not a valid index\n'.format(user_input))
            address = options[selected_index - 1]
        else:
            parser.error("No paired device found")

    args.channels = sorted(map(int, args.channels.split(",")))

    scientisst = ScientISST(address, log=args.log)
    scientisst.version()

    if args.fs == 1:
        num_frames = 1
    else:
        num_frames = args.fs // 5

    if args.stream:
        # import pylsl
        from pylsl import StreamInfo, StreamOutlet, local_clock

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
        f = __init_file(args.output, address, args.fs, args.channels)
        file_buffer = Queue()
        file_event = Event()
        file_thread = Thread(target=__write_frames, args=(f, file_buffer, file_event))
        file_thread.start()

    stop_event = Event()

    scientisst.start(args.fs, args.channels)
    if args.stream:
        lsl_thread.start()

    sys.stdout.write("Start acquisition\n")

    stream = False
    if args.duration > 0:
        run_scheduled_task(args.duration, stop_event)
    try:
        if args.verbose:
            header = "\t".join(__get_header(args.channels))
            sys.stdout.write("{}\n".format(header))
        while not stop_event.is_set():
            frames = scientisst.read(num_frames)
            if args.stream:
                lsl_buffer.put(frames)
            if args.output:
                file_buffer.put(frames)
            if args.verbose:
                sys.stdout.write("{}\n".format(frames[0]))
    except KeyboardInterrupt:
        pass
    sys.stdout.write("Stop acquisition\n")
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

    sys.stdout.write("Start LSL stream\n")
    while not event.is_set():
        if not buffer.empty():
            frames = buffer.get()

            chunk = [frame.a for frame in frames]

            current_index = frames[-1].seq
            lost_frames = current_index - ((previous_index + num_frames) & 15)

            if lost_frames > 0:
                timestamp = local_clock()
            else:
                timestamp += num_frames * dt

            previous_index = current_index
            outlet.push_chunk(chunk, timestamp)
            frames = None
        else:
            time.sleep(0.2)

    sys.stdout.write("Stop LSL stream\n")


def __get_metadata(address, fs, channels):
    metadata = {
        "Address": address,
        "Channels": __get_channel_labels(channels),
        "Channels indexes": channels,
        "Header": __get_header(channels),
        "Resolution (bits)": [4, 1, 1, 1, 1] + __get_channel_resolutions(channels),
        "Sampling Rate (Hz)": fs,
        "Timestamp": time.time(),
    }
    return metadata


def __get_channel_resolutions(channels):
    channel_resolutions = []
    for ch in channels:
        if ch == AX1 or ch == AX2:
            channel_resolutions += [24]
        else:
            channel_resolutions += [12]
    return channel_resolutions


def __get_channel_labels(channels):
    channel_labels = []
    for ch in channels:
        if ch == AX1 or ch == AX2:
            channel_labels += ["AX{}".format(ch)]
        else:
            channel_labels += ["AI{}".format(ch)]
    return channel_labels


def __get_header(channels):
    header = ["NSeq", "I1", "I2", "O1", "O2"]
    header += __get_channel_labels(channels)
    return header


def __init_file(filename, address, fs, channels):
    f = open(filename, "w")
    sys.stdout.write("Saving data to {}\n".format(filename))

    metadata = __get_metadata(address, fs, channels)
    header = "\t".join(metadata["Header"])

    f.write("#{}\n".format(metadata))
    f.write("#{}\n".format(header))
    return f


def __write_frames(f, buffer, event):
    while not event.is_set():
        if not buffer.empty():
            frames = buffer.get()
            f.write("\n".join(map(str, frames)) + "\n")
        else:
            time.sleep(0.2)
    f.close()


def __get_device_options():
    if sys.platform == "linux":
        options = __get_linux_bth_devices()
        return list(map(lambda option: option["addr"], options)), list(
            map(
                lambda option: "{} - {}".format(option["name"], option["addr"]), options
            )
        )
    else:
        import serial.tools.list_ports

        ports = serial.tools.list_ports.comports()
        options = []
        labels = []
        for port, desc, hwid in sorted(ports):
            if "scientisst" in port.lower():
                options += [port]
                labels += ["{} - {}".format(desc, port)]
        return options, labels


def __get_linux_bth_devices():
    import dbus

    def proxyobj(bus, path, interface):
        """commodity to apply an interface to a proxy object"""
        obj = bus.get_object("org.bluez", path)
        return dbus.Interface(obj, interface)

    def filter_by_interface(objects, interface_name):
        """filters the objects based on their support
        for the specified interface"""
        result = []
        for path in objects.keys():
            interfaces = objects[path]
            for interface in interfaces.keys():
                if interface == interface_name:
                    result.append(path)
        return result

    bus = dbus.SystemBus()

    # we need a dbus object manager
    manager = proxyobj(bus, "/", "org.freedesktop.DBus.ObjectManager")
    objects = manager.GetManagedObjects()

    # once we get the objects we have to pick the bluetooth devices.
    # They support the org.bluez.Device1 interface
    devices = filter_by_interface(objects, "org.bluez.Device1")

    # now we are ready to get the informations we need
    bt_devices = []
    for device in devices:
        obj = proxyobj(bus, device, "org.freedesktop.DBus.Properties")
        name = str(obj.Get("org.bluez.Device1", "Name"))
        if "scientisst" in name.lower():
            bt_devices.append(
                {
                    "name": name,
                    "addr": str(obj.Get("org.bluez.Device1", "Address")),
                }
            )
    return bt_devices


if __name__ == "__main__":
    main(sys.argv)
