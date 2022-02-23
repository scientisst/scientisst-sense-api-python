# import pylsl
from pylsl import StreamInfo, StreamOutlet, local_clock
from threading import Thread, Event
from queue import Queue
import sys
import time


class StreamLSL:
    def __init__(self, channels, fs, address, num_frames):
        self.info = StreamInfo(
            "ScientISST Sense",
            "RAW",
            len(channels),
            fs,
            "int32",
            address,
        )
        self.num_frames = num_frames
        self.buffer = Queue()
        self.event = Event()
        self.thread = Thread(target=self.__send_lsl)

    def __send_lsl(self):
        # make outlet
        outlet = StreamOutlet(self.info, chunk_size=self.num_frames)

        timestamp = local_clock()
        previous_index = -1
        dt = 1 / self.info.nominal_srate()
        frames = None

        sys.stdout.write("Start LSL stream\n")
        while not self.event.is_set():
            if not self.buffer.empty():
                frames = self.buffer.get()

                chunk = [frame.a for frame in frames]

                current_index = frames[-1].seq
                lost_frames = current_index - ((previous_index + self.num_frames) & 15)

                if lost_frames > 0:
                    timestamp = local_clock()
                else:
                    timestamp += self.num_frames * dt

                previous_index = current_index
                outlet.push_chunk(chunk, timestamp)
                frames = None
            else:
                time.sleep(0.2)

        sys.stdout.write("Stop LSL stream\n")

    def start(self):
        self.thread.start()

    def put(self, frames):
        self.buffer.put(frames)

    def stop(self):
        self.event.set()
