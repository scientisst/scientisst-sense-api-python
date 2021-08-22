import sys
import bluetooth
from scientisst.scientisst import *
import matplotlib.pyplot as plt
from threading import Timer
import sys

DURATION=5
recording=False

def run_scheduled_task(scientisst,DURATION):
    timer = Timer(DURATION, stop, [scientisst])
    timer.start()

def stop(scientisst):
    global recording
    recording=False
    scientisst.stop()
    scientisst.disconnect()
    sys.exit(0)


if __name__ == "__main__":

    # find()
    scientisst = ScientISST("4C:11:AE:88:84:5A")
    scientisst.version()

    fs = 100
    if fs == 1:
        num_frames = 1
    else:
        num_frames = fs // 5

    scientisst.start(fs, [AI1], "output.csv", False, API_MODE_SCIENTISST)
    recording=True
    print("Start acquisition")

    if DURATION>0:
        run_scheduled_task(scientisst,DURATION)
    try:
        with open("output.csv","w") as f:
            f.write("NSeq, I1, I2, O1, O2, AI1, AI2, AI3, AI4, AI5, AI6\n")
            while recording:
                frames = scientisst.read(num_frames)
                [f.write(frame.print() + "\n") for frame in frames]
                print(frames[0].print())
    except KeyboardInterrupt:
        print("Stop acquisition")
        stop(scientisst)
