# import pylsl
from pylsl import StreamInfo, StreamOutlet, local_clock
import sys

from sense_src.thread_builder import ThreadBuilder


class StreamLSL(ThreadBuilder):
    def __init__(self, channels, fs, address):
        super().__init__()
        self.info = StreamInfo(
            "ScientISST Sense",
            "RAW",
            len(channels),
            fs,
            "int32",
            address,
        )

    def start(self):
        # make outlet
        self.outlet = StreamOutlet(self.info)

        self.timestamp = local_clock()
        self.previous_index = -1
        self.dt = 1 / self.info.nominal_srate()

        sys.stdout.write("Start LSL stream\n")

        super().start()

    def thread_method(self, frames):
        chunk = [frame.a for frame in frames]
        num_frames = len(chunk)

        current_index = frames[-1].seq
        lost_frames = current_index - ((self.previous_index + num_frames) & 15)

        if lost_frames > 0:
            self.timestamp = local_clock()
        else:
            self.timestamp += num_frames * self.dt

        self.previous_index = current_index
        self.outlet.push_chunk(chunk, self.timestamp)
