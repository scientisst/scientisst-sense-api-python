from threading import Thread, Event
from queue import Queue
import time


class ThreadBuilder:
    def __init__(self):
        self.buffer = Queue()
        self.event = Event()
        self.thread = Thread(target=self.target)

    def start(self):
        self.thread.start()

    def put(self, frames):
        self.buffer.put(frames)

    def stop(self):
        # let the thread method finish before stop
        time.sleep(0.25)
        self.event.set()

    def target(self):
        while not self.event.is_set():
            if not self.buffer.empty():
                frames = self.buffer.get()
                self.thread_method(frames)
            else:
                time.sleep(0.1)

    def thread_method(self, frames):
        pass
