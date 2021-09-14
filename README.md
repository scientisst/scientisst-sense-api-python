
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
sudo rfcomm connect XX:XX:XX:XX:XX &
```

You can now simply run the `main.py` script:
```sh
python main.py
```

You can provide a duration on the script file, or simply hit `CTRL-C` when you wish to stop.

### Windows

Not tested yet.

## Plot

Dependencies:
- pandas
- numpy
- matplotlib

```sh
python plot_output.py
```

![Example ECG](https://raw.githubusercontent.com/scientisst/scientisst-sense-api-py/main/example-plot.png)
