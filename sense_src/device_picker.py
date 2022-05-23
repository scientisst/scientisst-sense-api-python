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
            name = "unkown"
            try:
                name = str(obj.Get("org.bluez.Device1", "Name"))
            except:
                pass
            if "scientisst" in name.lower():
                bt_devices.append(
                    {
                        "name": name,
                        "addr": str(obj.Get("org.bluez.Device1", "Address")),
                    }
                )
        return bt_devices
