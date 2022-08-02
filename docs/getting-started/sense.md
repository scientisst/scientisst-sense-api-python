`sense.py` is a script that simplifies the interaction with the ScientISST Sense.

It allows the selection of channels, sampling rate, and duration right from the command line.

It also implements file data saving in the background (using a different thread) and also streaming via Lab Streaming Layer (LSL).

## Usage Options

```
$ python sense.py -h

usage: sense.py [args] address

description: The program connects to the ScientISST Sense device and starts an acquisition, providing the option to store the received data in a .csv file.

positional arguments:
  address               For BTH communication:
                                Linux: BTH MAC address
                                Mac: serial port address
                                Windows: BTH serial COM port
                        For TCP/UDP communication:
                                All plataforms: server port.

options:
  -h, --help            show this help message and exit
  -f FS, --frequency FS
                        sampling frequency, default: 1000
  -c CHANNELS, --channels CHANNELS
                        analog channels, default: 1,2,3,4,5,6
  -d DURATION, --duration DURATION
                        duration in seconds, default: unlimited
  -o OUTPUT, --output OUTPUT
                        write report to output file, default: None
  -r, --raw             do not convert from raw to mV
  -s, --lsl             stream data using Lab Streaming Layer protocol. Use `python -m pylsl.examples.ReceiveAndPlot` to view stream
  --script SCRIPT       send the received frames to a script that inherits the CustomScript class
  -q, --quiet           don't print ScientISST frames
  -v, --version         show sense.py version
  --verbose             log sent/received bytes
  -m MODE, --mode MODE  The communication mode. Currently supported modes: bt_classic, tcp, tcp_ap. Default: bt_classic
```

## Automatic Selection

1. Pair your device
2. Run:

   ```
   python sense.py
   ```

3. Select the device from the list displayed:

```
ScientISST devices:
[1] ScientISST-ab-de - 08:3A:F2:49:AB:DE
[2] ScientISST-ac-be - 08:3A:F2:49:AC:BE
Connect to:
```

Then hit `CTRL-C` when you wish to stop.

## Manual Selection

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

```
python sense.py COMX
```

## Examples

### Single Channel

The following snippet will start streaming channel `A1`:

```
python sense.py -c 1
```

### Frequency

The following snippet will start streaming channel `A1` at 100 Hz:

```
python sense.py -c 1 -f 100
```

### Multiple Channels

The following snippet will start streaming channels `A1`,`A2`,`A3`,`A4`:

```
python sense.py -c 1,2,3,4
```

### Save to File

The following snippet will start recording the default channels (`A1`,`A2`,`A3`,`A4`,`A5`,`A6`) to the file `output.csv`:

```
python sense.py -o output.csv
```

### Duration

The following snippet will start recording the default channels for **10 seconds**:

```
python sense.py -o output.csv -d 10
```

### Lab Streaming Layer

The following snippet will start streaming the default channels using **LSL**:

```
python sense.py -s
```

#### Visualize the streaming data using:

Taking advantage of the LSL, it is possible to plot the real-time data:

```
python -m pylsl.examples.ReceiveAndPlot
```

### Custom Script

It is possible to run custom code every time the `sense.py` script reads data from the device. To do so, create a file, _e.g._ `hello_world.py`, with your own class inheriting the [`CustomScript`](https://github.com/scientisst/scientisst-sense-api-python/blob/main/sense_src/custom_script.py) class:

```python
from sense import CustomScript

class HelloWorld(CustomScript):
    def on_init(self):
        print("Hello world!")

    def on_start(self):
        print("Run your custom code on start")

    def on_read(self, frames):
        print("Received %s frames" % len(frames))

    def on_stop(self):
        print("All done")
```

Then, you just have to provided its path:

```
python sense.py -d 1 -q --script hello_world.py
```

Output:

```
...
Connected!
Hello world!
Start acquisition
Run your custom code on start
Received 200 frames
Received 200 frames
Received 200 frames
Received 200 frames
Received 200 frames
Stop acquisition
All done
Disconnected
```
