import sys
import bluetooth
from scientisst.scientisst import *
import matplotlib.pyplot as plt

if __name__ == "__main__":

    # find()
    scientisst = ScientISST("4C:11:AE:88:84:5A")
    scientisst.version()

    fs = 5000
    scientisst.start(fs, [AI3], "output.csv", False, API_MODE_SCIENTISST)
    print("Start acquisition")

    if fs == 1:
        num_frames = 1
    else:
        num_frames = fs // 5
    try:
        while True:
            frames = scientisst.read(num_frames)
            print([frames[0].seq] + frames[0].digital + frames[0].a)
    except KeyboardInterrupt:
        print("Stop acquisition")
        scientisst.stop()
    sys.exit(0)
