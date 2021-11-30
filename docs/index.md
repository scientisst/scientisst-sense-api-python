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
$ python sense.py -h

usage: sense.py [args] address

description: The program connects to the ScientISST Sense device and starts an acquisition, providing the option to store the received data in a .csv file.

positional arguments:  address               Linux: bluetooth MAC address, Mac: serial port address, Windows: bluetooth serial COM port

optional arguments:
  -h, --help            show this help message and exit
  -f FS, --frequency FS
                        sampling frequency, default: 1000
  -c CHANNELS, --channels CHANNELS
                        analog channels, default: 1,2,3,4,5,6
  -d DURATION, --duration DURATION
                        duration in seconds, default: unlimited
  -o OUTPUT, --output OUTPUT
                        write report to output file, default: None
  -s, --lsl             stream data using Lab Streaming Layer protocol
  -q, --quiet           don't print ScientISST frames
  -v, --verbose         log sent/received bytes
```

Simply hit `CTRL-C` when you wish to stop.

Example usage to acquire AI1 at 10Hz sample rate:

```
python3 sense.py -f 10 -c 1 08:3A:F2:49:AC:D2 -o output.csv
```

### Linux

Pair and trust the ScientISST Sense board:

```sh
bluetoothctl
scan on
pair XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX
```

You can now run the `sense.py` script:
```sh
python sense.py XX:XX:XX:XX:XX
```



### Mac

First, you need to pair the ScientISST sense device in the Bluetooth Settings section.
Then, you'll need to find the serial port address using the Terminal:

```sh
ls /dev/tty.ScientISST*
```

Copy the `String` like: `/dev/tty.ScientISST-XX-XX-SPP_SE`.

You can now run the `sense.py` script:

```sh
python sense.py /dev/tty.ScientISST-XX-XX-SPP_SE
```



### Windows

Turn the ScientISST Sense board on.

Now, go to Control Panel > Hardware and Sound > Devices and Printers. Select "Add a device". Select the ScientISST Sense board, hit "next" until its set up.

While connected to the board, search "Bluetooth settings" on the Control Panel, then go to the "COM ports" tab and check the port name for the **outgoing** entry. Copy the `String` like: `COMX`

You can now run the `sense.py` script:

```sh
python sense.py COMX
```


## Plot

Dependencies:
- pandas
- numpy
- matplotlib

```sh
python plot_output.py
```

![Example ECG](https://raw.githubusercontent.com/scientisst/scientisst-sense-api-py/main/example-plot.png)
