import sys
from scientisst.scientisst import AX1, AX2
from sense.thread_builder import ThreadBuilder
from datetime import datetime


class FileWriter(ThreadBuilder):
    def __init__(self, filename, address, fs, channels, mv):
        super().__init__()
        self.filename = filename
        self.address = address
        self.fs = fs
        self.channels = channels
        self.mv = mv

    def start(self):
        self.__init_file()
        super().start()

    def stop(self):
        super().stop()
        self.f.close()

    def thread_method(self, frames):
        self.f.write("\n".join(map(str, frames)) + "\n")

    def __init_file(
        self,
    ):
        self.f = open(self.filename, "w")
        sys.stdout.write("Saving data to {}\n".format(self.filename))

        metadata = self.__get_metadata(self.address, self.fs, self.channels)
        header = "\t".join(metadata["Header"])

        self.f.write("#{}\n".format(metadata))
        self.f.write("#{}\n".format(header))

    def __get_metadata(self, address, fs, channels):
        timestamp = datetime.now()
        metadata = {
            "Channels": channels,
            "Channels labels": get_channel_labels(channels, self.mv),
            "Device": address,
            "Header": get_header(channels, self.mv),
            "Resolution (bits)": [4, 1, 1, 1, 1] + self.__get_channel_resolutions(),
            "Sampling Rate (Hz)": fs,
            "Timestamp": timestamp.timestamp(),
            "ISO 8601": timestamp.isoformat(),
        }
        if self.mv:
            metadata["Channels indexes raw"] = list(
                map(lambda x: (x - 1) * 2 + 5, channels)
            )
            metadata["Channels indexes mV"] = list(
                map(lambda x: (x - 1) * 2 + 6, channels)
            )
        else:
            metadata["Channels indexes"] = list(map(lambda x: x + 5, channels))

        sorted_metadata = {}
        for key in sorted(metadata):
            sorted_metadata[key] = metadata[key]

        return sorted_metadata

    def __get_channel_resolutions(self):
        channel_resolutions = []
        for ch in self.channels:
            if ch == AX1 or ch == AX2:
                channel_resolutions += [24]
            else:
                channel_resolutions += [12]
        return channel_resolutions

    def __get_channel_resolutions_mv(self):
        channel_resolutions = []
        for ch in self.channels:
            if ch == AX1 or ch == AX2:
                channel_resolutions += [0.4]
            else:
                channel_resolutions += [0.8]
        return channel_resolutions


def get_channel_labels(channels, mv):
    channel_labels = []
    for ch in channels:
        if not mv:
            if ch == AX1 or ch == AX2:
                channel_labels += ["AX{}".format(ch)]
            else:
                channel_labels += ["AI{}".format(ch)]
        else:
            if ch == AX1 or ch == AX2:
                channel_labels += ["AX{}_raw".format(ch)]
                channel_labels += ["AX{}_mv".format(ch)]
            else:
                channel_labels += ["AI{}_raw".format(ch)]
                channel_labels += ["AI{}_mv".format(ch)]
    return channel_labels


def get_header(channels, mv):
    header = ["NSeq", "I1", "I2", "O1", "O2"]
    header += get_channel_labels(channels, mv)
    return header
