import sys
from argparse import ArgumentParser


class ArgParser:
    class MyParser(ArgumentParser):
        def error(self, message):
            sys.stderr.write("error: %s\n\n" % message)
            self.print_help()
            sys.exit(2)

    def __init__(self):
        usage = "%(prog)s [args] address"
        description = "description: The program connects to the ScientISST Sense device and starts an acquisition, providing the option to store the received data in a .csv file."
        self.parser = self.MyParser(usage=usage, description=description)

        self.parser.add_argument(
            "address",
            nargs="?",
            type=str,
            help="Linux: bluetooth MAC address, Mac: serial port address, Windows: bluetooth serial COM port",
        )
        self.parser.add_argument(
            "-f",
            "--frequency",
            dest="fs",
            help="sampling frequency, default: 1000",
            type=int,
            default=1000,
        )
        self.parser.add_argument(
            "-c",
            "--channels",
            dest="channels",
            type=str,
            help="analog channels, default: 1,2,3,4,5,6",
            default="1,2,3,4,5,6",
        )
        self.parser.add_argument(
            "-d",
            "--duration",
            dest="duration",
            help="duration in seconds, default: unlimited",
            type=int,
            default=0,
        )
        self.parser.add_argument(
            "-o",
            "--output",
            dest="output",
            help="write report to output file, default: None",
            type=str,
            default=None,
        )
        self.parser.add_argument(
            "-r",
            "--raw",
            action="store_false",
            dest="convert",
            default=True,
            help="do not convert from raw to mV",
        )
        self.parser.add_argument(
            "-s",
            "--lsl",
            dest="stream",
            action="store_true",
            default=False,
            help="stream data using Lab Streaming Layer protocol. Use `python -m pylsl.examples.ReceiveAndPlot` to view stream",
        )
        self.parser.add_argument(
            "--script",
            dest="script",
            help="send the received frames to a script that inherits the CustomScript class",
            type=str,
            default=None,
        )
        self.parser.add_argument(
            "-q",
            "--quiet",
            action="store_false",
            dest="verbose",
            default=True,
            help="don't print ScientISST frames",
        )
        self.parser.add_argument(
            "-v",
            "--version",
            dest="version",
            action="store_true",
            default=False,
            help="show sense.py version",
        )
        self.parser.add_argument(
            "--verbose",
            dest="log",
            action="store_true",
            default=False,
            help="log sent/received bytes",
        )
        self.parser.add_argument(
            "--rt_signals",
            dest="rt_signals",
            default=True,
            help="If true, real-time plotting of raw voltage is enabled for the selected analog channels.",
        )
        self.args = self.parser.parse_args()

    def error(self, value):
        self.parser.error(value)
