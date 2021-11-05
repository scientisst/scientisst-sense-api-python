class Frame:
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
