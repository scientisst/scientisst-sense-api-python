#!/usr/bin/python

"""
sense.py
"""

VERSION = "0.0.2"

import sys
from scientisst import *
from threading import Timer
from threading import Thread, Event
from queue import Queue
from sense.arg_parser import ArgParser

from sense.lsl import StreamLSL
from sense.writer import *


def run_scheduled_task(DURATION, stop_event):
    timer = Timer(DURATION, stop, [stop_event])
    timer.start()


def stop(stop_event):
    stop_event.set()


def main(argv):

    arg_parser = ArgParser()
    args = arg_parser.args

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
        # create LSL stream info
        lsl = StreamLSL(
            args.channels,
            args.fs,
            address,
            num_frames,
        )

    if args.output:
        writer = Writer(args.output, address, args.fs, args.channels)

    stop_event = Event()

    scientisst.start(args.fs, args.channels)
    if args.stream:
        lsl.start()
    if args.output:
        writer.start()

    sys.stdout.write("Start acquisition\n")

    if args.duration > 0:
        run_scheduled_task(args.duration, stop_event)
    try:
        if args.verbose:
            header = "\t".join(get_header(args.channels)) + "\n"
            sys.stdout.write(header)
        while not stop_event.is_set():
            frames = scientisst.read(num_frames)
            if args.stream:
                lsl.put(frames)
            if args.output:
                writer.put(frames)
            if args.verbose:
                sys.stdout.write("{}\n".format(frames[0]))
    except KeyboardInterrupt:
        pass
    sys.stdout.write("Stop acquisition\n")
    if args.stream:
        lsl.stop()
    if args.output:
        writer.stop()

    scientisst.stop()
    scientisst.disconnect()

    sys.exit(0)


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
