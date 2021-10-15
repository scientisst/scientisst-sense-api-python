
# scientisst-sense-api-python

The ScientISST SENSE Python API

## Dependencies

- PySerial

Install it using `pip`:

```sh
pip install pyserial
```

## Installing

```sh
# Getting this repository 
git clone https://github.com/scientisst/scientisst-sense-api-python.git
```

## Running

```
$ python main.py -h
Usage: main.py [options]

Options:
  -h, --help            show this help message and exit  -a ADDRESS, --address=ADDRESS
                        device serial port ADDRESS, default: /dev/rfcomm0  -f FS, --frequency=FS
                        sampling FREQUENCY, default: 1000  -c CHANNELS, --channels=CHANNELS
                        analog CHANNELS, default: [1, 2, 3, 4, 5, 6]
  -d DURATION, --duration=DURATION
                        DURATION in seconds, default: unlimited
  -o OUTPUT, --output=OUTPUT
                        write report to OUTPUT file, default: None
  -q, --quiet           don't print ScientISST frames
```

### Mac

First, you need to pair the ScientISST sense device in the Bluetooth Settings section.
Then, you'll need to find the serial port address using the Terminal:

```sh
ls /dev/tty.ScientISST*
```

Copy the `String` like: `/dev/tty.ScientISST-XX-XX-SPP_SE` and replace it in the `main.py` file:

```sh
scientisst = ScientISST("/dev/tty.ScientISST-XX-XX-SPP_SE")
```

You can now simply run the `main.py` script:
```sh
python main.py
```

You can provide a duration on the script file, or simply hit `CTRL-C` when you wish to stop.


### Linux

#### Open Serial Port

Pair and trust the ScientISST Sense board:

```sh
bluetoothctl
scan on
pair XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX
```

Now open a serial port with the device and leave the command running:

```sh
sudo rfcomm connect hci0 XX:XX:XX:XX:XX &
```

You can now simply run the `main.py` script:
```sh
python main.py
```

You can provide a duration on the script file, or simply hit `CTRL-C` when you wish to stop.

### Windows

Turn the ScientISST Sense board on.

Now, go to Control Panel > Hardware and Sound > Devices and Printers. Select "Add a device". Select the ScientISST Sense board, hit "next" until its set up.

While connected to the board, search "Bluetooth settings" on the Control Panel, then go to the "COM ports" tab and check the port name for the **outgoing** entry. Type the `String` like: `COMX` and replace it in the main.py file:

```sh
scientisst = ScientISST("COMX")
```

You can now simply run the `main.py` script:

```sh
python main.py
```

You can provide a duration on the script file, or simply hit `CTRL-C` when you wish to stop.
## Plot

Dependencies:
- pandas
- numpy
- matplotlib

```sh
python plot_output.py
```

![Example ECG](https://raw.githubusercontent.com/scientisst/scientisst-sense-api-py/main/example-plot.png)
