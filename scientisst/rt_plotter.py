# imports
import sys
import pyqtgraph as pg
import threading
from collections import deque
from PyQt5.QtCore import *
from functools import partial
from PyQt5.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QLabel
from sense.file_writer import get_header
from sense.thread_builder import *


class MainWindow(QMainWindow):
    signal_data_1 = pyqtSignal(object)
    signal_data_2 = pyqtSignal(object)
    signal_data_3 = pyqtSignal(object)
    signal_data_4 = pyqtSignal(object)
    signal_data_5 = pyqtSignal(object)
    signal_data_6 = pyqtSignal(object)

    def __init__(self, stop_event, scientisst, args, lsl_buffer=None, file_buffer=None, parent=None):
        """Class that starts a real-time plot for the analog channels.

            Args:
                stop_event (threading.Event): The stopping stimulus.
                scientisst (scientISST): The ScientISST device.
                args (arg_parser.args): The arguments parsed to the script.
                lsl_buffer (streamLSL): The optional LSL buffer. If not streaming, it's None.
                file_buffer (FileWriter): The optional File buffer. If saving output, it's None.
                parent (QWdiget): The parent widget. None as default.

        """

        super(MainWindow, self).__init__(parent)

        length = 100

        header = get_header(args.channels, args.convert)
        analog_channels = args.channels

        analog_to_index = dict()
        for channel, i in zip(analog_channels, range(len(analog_channels))):
            if not args.convert:
                channel_str = "AI{}".format(channel)
                analog_to_index[channel_str] = header.index(channel_str)
                analog_channels[i] = channel_str
                str_unit = 'raw'
            else:
                # if convert to mV, use mV-converted signals
                channel_str = "AI{}_mv".format(channel)
                analog_to_index[channel_str] = header.index(channel_str)
                analog_channels[i] = channel_str
                str_unit = 'mV'

        self.setWindowTitle('Real-time plotter, channels ({}): {}'.format(str_unit, ", ".join(analog_channels)))

        # number of analog channels
        self.n_channels = len(analog_channels)
        self.signal_inds = [analog_to_index[x] for x in analog_channels]

        # creating a list of buffers
        self.signal_data_buffers = [deque([1.] * length, length) for _ in range(self.n_channels)]

        # time buffer will be the same for all signals (we use the same display sampling frequency)
        self.timebuffer = deque([0.] * length, length)

        self.connected = False

        # scientisst acquisition variables
        self.stop_event = stop_event
        self.scientisst = scientisst

        self.num_frames = scientisst.number_of_frames()

        # scientisst lsl and file buffers
        self.lsl_buffer = lsl_buffer
        self.file_buffer = file_buffer

        self.stream = args.stream
        self.output = args.output

        QTimer.singleShot(0, self.startThread)
        self.cwidget = QWidget()
        vb = QVBoxLayout()

        plot_widgets = []
        self.curves = []

        spaced_str = ' ' * 10
        self.lblNames = []

        for i in range(self.n_channels):
            plot_widgets.append(pg.PlotWidget())
            str_ = '{}{}'.format(spaced_str, analog_channels[i])
            self.lblNames.append(QLabel(str_, plot_widgets[i]))
            self.lblNames[i].setStyleSheet('color: white')
            vb.addWidget(plot_widgets[-1])

        self.cwidget.setLayout(vb)
        self.setCentralWidget(self.cwidget)

        for i in range(self.n_channels):
            self.curves.append(plot_widgets[i].plot(pen=(200, 200, 200), symbolBrush=(255, 0, 0), symbolPen='w'))
            self.curves[i].setData(self.signal_data_buffers[i], self.signal_data_buffers[i])

        self.signal_data_pack = []

        # temporary mapping to the 6 instantiated `pyqtSignal` objects
        _signal_data_pack = {0: self.signal_data_1,
                             1: self.signal_data_2,
                             2: self.signal_data_3,
                             3: self.signal_data_4,
                             4: self.signal_data_5,
                             5: self.signal_data_6}

        for i in range(self.n_channels):
            _signal_data_pack[i].connect(partial(self.onNewData, signal_index=i))
            self.signal_data_pack.append(_signal_data_pack[i])

        self.convert = args.convert

        # if time == 0, the app closes when the user wants
        if args.duration != 0:
            self.time_to_wait = args.duration + 3

            self.timer = QTimer()
            self.timer.setInterval(1000)
            self.timer.timeout.connect(self.auto_closing)
            self.timer.start()

    def onNewData(self, signal, signal_index=0):
        if self.timebuffer[0] != 0:
            self.curves[signal_index].setData(self.timebuffer, signal)
            for x in self.lblNames:
                x.setText("<span style='color: green'>y2=%0.1f</span>" % str(signal))

        else:
            self.curves[signal_index].setData(signal)

    def startThread(self):
        thread = threading.Thread(target=self.read_data_pair,
                                  args=(self.stop_event, self.scientisst, self.stream, self.output, True))
        # Makes sures that the thread stops when exiting the program
        thread.setDaemon(True)
        thread.start()
        self.tstart = time.perf_counter()

    def stopThread(self):
        print('Stop the thread...')

    def handle_data(self, data):
        packet = data[::100]
        data = []

        try:
            for i in range(self.n_channels):
                data.append([float(x.__str__().split('\t')[self.signal_inds[i]]) for x in packet])

        except ValueError:
            for i in range(self.n_channels):
                data.append([0. for _ in packet])

        for i in range(self.n_channels):
            self.signal_data_buffers[i].extend(data[i])
            self.signal_data_pack[i].emit(self.signal_data_buffers[i])

        t = time.perf_counter()
        dt = t - self.tstart
        self.timebuffer.append(dt)

    def read_data_pair(self, stop_event, scientisst, stream, output, verbose=True):
        try:
            while not stop_event.is_set():
                frames = scientisst.read(convert=self.convert)

                self.handle_data(frames)
                sys.stdout.write("{}\n".format(frames[0]))

                if stream:
                    self.lsl_buffer.put(frames)
                if output:
                    self.file_buffer.put(frames)
                if verbose:
                    sys.stdout.write("{}\n".format(frames[0]))

        except:
            self.close()

    def auto_closing(self, verbose=False):
        if verbose:
            print("Closing in {0} secondes.".format(self.time_to_wait))
        self.time_to_wait -= 1
        if self.time_to_wait <= 0:
            self.close()

    def closeEvent(self, event):
        if self.okToContinue():
            event.accept()
            self.stopThread()
        else:
            event.ignore()

    def okToContinue(self):
        return True

    def get_file_buffer(self):
        return self.file_buffer

    def get_lsl_buffer(self):
        return self.lsl_buffer
