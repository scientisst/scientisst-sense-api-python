class Frame:
    digital = [0] * 4
    seq = -1
    a = [0] * 8

    def toMap(self):
        return {"sequence": self.seq, "analog": self.a, "digital": self.digital}

    def toString(self):
        return str(self.toMap())

    def print(self):
        return ", ".join(map(str,[self.seq] + self.digital + self.a))
