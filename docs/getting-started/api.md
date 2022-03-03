## Examples

### Connect to Device

The following code creates a [`Scientisst`][scientisst.scientisst.ScientISST] object and establishes a connection to the specified device.

```python
scientisst = ScientISST("08:3A:F2:49:AB:DE")
```

### Print Version

The following code prints the firmware version of the device connected with the previous command.

```python
scientisst.version()
```

### Acquisition

The following snippet starts streaming data from channels `A1`, `A2`, and `A3` at 100 Hz.

Then, it reads the streaming data (by default, for frequencies not too high, 5 times per second) and prints the first [`Frame`][scientisst.frame.Frame].

After reading 1000 frames, it stops the acquisition.

```python
scientisst.start(100, [1, 2, 3])

for i in range(50):
    frames = scientisst.read()
    print(frames[0])

scientisst.stop()
```

### Disconnect

Once you no longer want to use the ScientISST device, you must dispose it:

```python
scientisst.disconnect()
```
