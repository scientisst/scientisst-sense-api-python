class Frame:
    """
    ScientISST Device Frame class

    A frame returned by ScientISST.read()

    Attributes:
        seq (int): Frame sequence number (0...15).

            This number is incremented by 1 on each consecutive frame, and it overflows to 0 after 15 (it is a 4-bit number).

            This number can be used to detect if frames were dropped while transmitting data.

        digital (list): Array of digital ports states (False for low level or True for high level).

            On original ScientISST, the array contents are: I1 I2 I3 I4.

            On ScientISST 2, the array contents are: I1 I2 O1 O2.

        a (list): Array of analog inputs values of the active channles.

            If all channels are active, `a` will have 8 elements: 6 AIs and 2 AXs.
    """

    digital = [0] * 4
    seq = -1
    a = None

    def __init__(self, num_frames):
        self.a = [None] * num_frames

    def toMap(self):
        return {"sequence": self.seq, "analog": self.a, "digital": self.digital}

    def toString(self):
        return str(self.toMap())

    def __str__(self):
        return "{}, {}, {}, {}, {}, {}".format(
            self.seq,
            self.digital[0],
            self.digital[1],
            self.digital[2],
            self.digital[3],
            ", ".join(map(str, self.a)),
        )
