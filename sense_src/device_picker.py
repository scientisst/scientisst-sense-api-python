import sys


class DevicePicker:
    def select_device(self):
        options, labels = self.__get_device_options()
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
            return options[selected_index - 1]

    def __get_device_options(self):
        if sys.platform == "linux":
            options = self.__get_linux_bth_devices()
            return list(map(lambda option: option["addr"], options)), list(
                map(
                    lambda option: "{} - {}".format(
                        option["name"] if "name" in option else "unnamed",
                        option["addr"],
                    ),
                    options,
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
                    label = ""
                    if desc != "n/a":
                        label += "{} - ".format(desc)
                    labels += [label + port]
            return options, labels

    def __get_linux_bth_devices(self):

        import pydbus

        bt_devices = {}

        bus = pydbus.SystemBus()
        mngr = bus.get("org.bluez", "/")

        mngd_objs = mngr.GetManagedObjects()
        for path in mngd_objs:
            addr = mngd_objs[path].get("org.bluez.Device1", {}).get("Address")
            name = mngd_objs[path].get("org.bluez.Device1", {}).get("Name")

            if name and "scientisst" in name.lower() and addr not in bt_devices:
                bt_devices[addr] = {
                    "name": name,
                    "addr": addr,
                }

        return bt_devices.values()
