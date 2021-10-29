from sys import platform
if platform=='linux':
    import socket
else:
    import serial

import time
from math import log2

from scientisst.frame import *
from scientisst.state import *
from scientisst.exceptions import *

TIMEOUT_IN_SECONDS = 10

# API_MODE
API_MODE_BITALINO = 1
API_MODE_SCIENTISST = 2
API_MODE_JSON = 3

# CHANNELS
AI1 = 1
AI2 = 2
AI3 = 3
AI4 = 4
AI5 = 5
AI6 = 6
AX1 = 7
AX2 = 8


class ScientISST:
    """
    ScientISST Device class

    Parameters
    ----------
    address : String
        The device serial port address ("/dev/example")
    serial_speed : int
        The serial port bitrate. Default: 115200 bit/s.
    log : bool
        If the bytes sent and received should be showed. Default: False.
    """

    __serial = None
    __socket = None
    __num_chs = 0
    __api_mode = 1
    __sample_rate = None
    __chs = [None] * 8
    __f = None
    __log = False

    def __init__(self, address, serial_speed = 115200, log=False, api=API_MODE_SCIENTISST):
        self.address = address
        self.speed = serial_speed
        self.__log = log

        print("Connecting to device...")
        # Create the client socket
        if platform == 'linux':
            self.__socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.__socket.settimeout(TIMEOUT_IN_SECONDS)
            self.__socket.connect((address, 1))
        else:
            self.__serial = serial.Serial(address, serial_speed, timeout=TIMEOUT_IN_SECONDS)

        print("Connected!")

        if api != API_MODE_SCIENTISST and api != API_MODE_JSON and api != API_MODE_BITALINO:
            raise InvalidParameterError();
        # Set API mode
        self.__changeAPI(api)

    def version(self):
        """
        Gets the device firmware version string

        Parameters
        ----------
        void

        Returns
        -------
        version : string
            Firmware version
        """
        if self.__api_mode == API_MODE_BITALINO:
            header = "BITalino"
        else:
            header = "ScientISST"
        headerLen = len(header)

        cmd = b"\x07"
        self.__send(cmd)
        version = ""
        while True:
            result = self.__recv(1)
            if result:
                if len(version) >= headerLen:
                    if (self.__api_mode == API_MODE_BITALINO and result == b"\n") or result == b"\x00":
                        break
                    elif result != b"\n":
                        version += result.decode("utf-8")
                else:
                    result = result.decode("utf-8")
                    if result is header[len(version)]:
                        version += result
                    else:
                        version = ""
                        if result == header[0]:
                            version += result
            else:
                return

        print("ScientISST version: {}".format(version))
        return version

    def start(
        self, sample_rate, channels, file_name=None, simulated=False,
    ):
        """
        Starts a signal acquisition from the device

        Parameters
        ----------
        sample_rate : int
            Sampling rate in Hz. Accepted values are 1, 10, 100 or 1000 Hz.
        channels : array
            Set of channels to acquire. Accepted channels are 1...6 for inputs A1...A6.
        file_name : string
            Name of the file where the live mode data will be written into.
        simulated : bool
            If true, start in simulated mode. Otherwise start in live mode. Default is to start in live mode.
        api : int
            The API mode, this API supports the ScientISST and JSON APIs.

        Returns
        -------
        void

        Exceptions
        ----------
        DeviceNotIdleError : if the device is already in acquisition mode.
        InvalidParameterError : if no valid API value is chosen or an incorrect array of channels is provided.
        """
        if self.__num_chs != 0:
            raise DeviceNotIdleError();

        # Set API mode
        self.__changeAPI(self.__api_mode)

        self.__sample_rate = sample_rate
        self.__num_chs = 0


        # Sample rate
        sr = 0b01000011
        sr |= self.__sample_rate << 8
        self.__send(sr,4)

        if not channels:  # channels is empty
            chMask = 0xFF  #  all 8 analog channels
            self.__num_chs = 8
        else:
            chMask = 0
            for ch in channels:
                if ch <= 0 or ch > 8:
                    raise InvalidParameterError()
                self.__chs[self.__num_chs] = ch  # Fill chs vector

                mask = 1 << (ch - 1)
                if chMask & mask:
                    raise InvalidParameterError()

                chMask |= mask
                self.__num_chs += 1

        # Cleanup existing data in bluetooth socket
        self.__clear()

        if simulated:
            cmd = 0x02
        else:
            cmd = 0x01
        cmd |= chMask << 8

        self.__send(cmd)

        self.__packet_size = self.__getPacketSize()

        # If file_name was provided, open file and write header
        if file_name:
            self.__initFile(file_name)

    def read(self, num_frames):
        """
        Reads acquisition frames from the device.
        This method returns when all requested frames are received from the device, or when a timeout occurs.

        Parameters
        ----------
        num_frames : int
           Number of frames to retrieve from the device

        Returns
        -------
        frames : array
            List of Frame objects retrieved from the device

        Exceptions
        ----------
        DeviceNotInAcquisitionError : if the device is not in acquisition mode.
        NotSupportedError : if the device API is in BITALINO mode
        UnknownError : if the device stopped sending frames for some unknown reason.
        """

        frames = [None] * num_frames

        if self.__num_chs == 0:
            raise DeviceNotInAcquisitionError()

        for it in range(num_frames):
            mid_frame_flag = 0
            bf = list(self.__recv(self.__packet_size))
            if not bf:
                if self.__f:
                    self.__closeFile()
                raise UnknownError("Esp stopped sending frames -> It stopped live mode on its own \n(probably because it can't handle this number of channels + sample rate)")

            #  if CRC check failed, try to resynchronize with the next valid frame
            while not self.__checkCRC4(bf, self.__packet_size):
                bf = bf[1:] + [None]
                #  checking with one new byte at a time
                result = self.__recv(1)
                bf[-1] = int.from_bytes(result, "big")

                if not bf[-1]:
                    return list(filter(lambda frame: frame, frames))   #  a timeout has occurred

            f = Frame()
            frames[it] = f
            if self.__api_mode == API_MODE_SCIENTISST:
                # Get seq number and IO states
                f.seq = bf[-1] >> 4
                for i in range(4):
                    f.digital[i] = (bf[-2] & (0x80 >> i)) != 0

                # Get channel values
                byte_it=0
                for i in range(self.__num_chs):
                    curr_ch = self.__chs[self.__num_chs - 1 - i]

                    # If it's an AX channel
                    if curr_ch == AX1 or curr_ch == AX2:
                        f.a[curr_ch-1] = (
                            int.from_bytes(bf[byte_it : byte_it + 4], byteorder="little") & 0xFFFFFF
                        )
                        byte_it += 3

                    # If it's an AI channel
                    else:
                        if not mid_frame_flag:
                            f.a[curr_ch - 1] = (
                                int.from_bytes(bf[byte_it : byte_it + 2], byteorder="little")
                                & 0xFFF
                            )
                            byte_it += 1
                            mid_frame_flag = 1
                        else:
                            f.a[curr_ch - 1] = (
                                int.from_bytes(bf[byte_it : byte_it + 2], byteorder="little") >> 4
                            )
                            byte_it += 2
                            mid_frame_flag = 0
            elif self.__api_mode == API_MODE_JSON:
                print(bf)
            # d.Parse((const char*)buffer);

            # f.seq = 1;

            # for(int i = 0; i < num_chs; i++){
            # sprintf(memb_name, "AI%d", chs[i]);
            # f.a[i] = strtol(d[memb_name].GetString(), &junk, 10);
            # }

            # f.digital[0] = strtol(d["I1"].GetString(), &junk, 10);
            # f.digital[1] = strtol(d["I2"].GetString(), &junk, 10);
            # f.digital[2] = strtol(d["O1"].GetString(), &junk, 10);
            # f.digital[3] = strtol(d["O2"].GetString(), &junk, 10);
            # }
            else:
                raise NotSupportedError()


        if self.__f:
            self.__writeFramesFile(frames)

        return frames

    def stop(self):
        """
        Stops a signal acquisition.

        Parameters
        ----------
        void

        Returns
        -------
        void

        Exceptions
        ----------
        DeviceNotInAcquisitionError : if the device is not in acquisition mode.
        """
        if self.__num_chs == 0:
            raise DeviceNotInAcquisitionError()

        cmd = b"\x00"
        self.__send(cmd)  # 0  0  0  0  0  0  0  0 - Go to idle mode

        self.__num_chs = 0
        self.__sample_rate = 0

        # Cleanup existing data in bluetooth socket
        self.__clear()

        if self.__f:
            self.__closeFile()

    def battery(self, value=0):
        """
        Sets the battery voltage threshold for the low-battery LED.

        Parameters
        ----------
        value : int
            Battery voltage threshold. Default value is 0.
            Value | Voltage Threshold
            ----- | -----------------
                0 |   3.4 V
             ...  |   ...
               63 |   3.8 V

        Returns
        -------
        void

        Exceptions
        ----------
        DeviceNotIdleError : if the device is in acquisition mode.
        InvalidParameterError : if an invalid battery threshold value is given.
        """
        if self.__num_chs != 0:
            raise DeviceNotIdleError()

        if value < 0 or value > 63:
            raise InvalidParameterError()

        cmd = value << 2
        # <bat threshold> 0 0 - Set battery threshold
        self.__send(cmd)

    def trigger(self, digital_output):
        """
        Assigns the digital outputs states.

        Parameters
        ----------
        digital_output : array
            Vector of booleans to assign to digital outputs, starting at first output (O1).

        Returns
        -------
        void

        Exceptions
        ----------
        InvalidParameterError : if the length of the digital_output array is different from 2.
        """
        length = len(digital_output)

        if length != 2:
            raise InvalidParameterError()

        cmd = 0xB3  # 1  0  1  1  O2 O1 1  1 - Set digital outputs

        for i in range(length):
            if digital_output[i]:
                cmd |= 0b100 << i

        self.__send(cmd)

    def dac(self, pwm_output):
        """
        Assigns the analog (PWM) output value (%ScientISST 2 only).

        Parameters
        ----------
        pwm_output : int
            Analog output value to set (0...255).

        Returns
        -------
        void

        Exceptions
        ----------
        InvalidParameterError : if the pwm_output value is outside of its range, 0-255.
        """
        if pwm_output < 0 or pwm_output > 255:
            raise InvalidParameterError()

        cmd = 0xA3  # 1  0  1  0  0  0  1  1 - Set dac output

        cmd |= pwm_output << 8
        self.__send(cmd)

    # TODO: test with ScientISST Sense v2
    def state(self):
        """
        Returns current device state (%ScientISST 2 only).

        Parameters
        ----------
        void

        Returns
        -------
        state : State
            Current device state

        Exceptions
        ----------
        DeviceNotIdleError : if the device is in acquisition mode.
        ContactingDeviceError : if there is an error contacting the device.
        """
        if self.__num_chs != 0:
            raise DeviceNotIdleError()

        cmd = 0x0B
        self.__send(cmd)
        # 0  0  0  0  1  0  1  1 - Send device status

        # if (recv(&statex, sizeof statex) != sizeof statex)    # a timeout has occurred
        # throw Exception(Exception::CONTACTING_DEVICE);
        result = self.__recv(16)
        if not result or not self.__checkCRC4(result, 16):
            raise ContactingDeviceError()

        state = State()
        print(result)

        # for(int i = 0; i < 6; i++)
        # state.analog[i] = statex.analog[i];

        # state.battery = statex.battery;
        # state.batThreshold = statex.batThreshold;

        # for(int i = 0; i < 4; i++)
        # state.digital[i] = ((statex.portsCRC & (0x80 >> i)) != 0);

        # return state;

    def disconnect(self):
        """
        Disconnects from a ScientISST device. If an aquisition is running, it is stopped

        Parameters
        ----------
        void

        Returns
        -------
        void
        """
        if self.__num_chs != 0:
            self.stop()
        if self.__socket:
            self.__socket.close()
            self.__socket = None
        else:
            self.__serial.close()
            self.__serial = None
        print("Disconnected")


    def __getPacketSize(self):
        packet_size = 0

        if self.__api_mode == API_MODE_SCIENTISST:
            num_intern_active_chs = 0
            num_extern_active_chs = 0

            for ch in self.__chs:
                if ch:
                    # Add 24bit channel's contributuion to packet size
                    if ch == AX1 or ch == AX2:
                        num_extern_active_chs += 1
                    # Count 12bit channels
                    else:
                        num_intern_active_chs += 1

            # Add 24bit channel's contributuion to packet size
            packet_size = 3 * num_extern_active_chs

            # Add 12bit channel's contributuion to packet size
            if not (num_intern_active_chs % 2):  # If it's an even number
                packet_size += (num_intern_active_chs * 12) / 8
            else:
                packet_size += (
                    (num_intern_active_chs * 12) - 4
                ) / 8  # -4 because 4 bits can go in the I/0 byte
            # for the I/Os and seq+crc bytes
            packet_size += 2

        elif self.__api_mode == API_MODE_JSON:
            for i in range(self.__num_chs):
                # If it's internal ch
                if self.__chs[i]<=6:
                    # sprintf(aux_str, "AI%d", chs[i]);
                    # member_name.SetString(aux_str, d.GetAllocator());
                    # member_value.SetString(value_internal_str, d.GetAllocator());
                    # d.AddMember(member_name, member_value, d.GetAllocator());
                    packet_size+=3  # AI%d
                    packet_size+=2  # 0-4095 = 12 bits <= 2 bytes
                else:
                    packet_size+=3  # AX%d
                    packet_size+=4  # 0-16777215 = 24 bits <= 4 bytes
            # Add IO state json objects
            # d.AddMember("I1", "0", d.GetAllocator());
            # d.AddMember("I2", "0", d.GetAllocator());
            # d.AddMember("O1", "0", d.GetAllocator());
            # d.AddMember("O2", "0", d.GetAllocator());
            packet_size += 3    # I1 + 0|1
            packet_size += 3    # I2 + 0|1
            packet_size += 3    # O1 + 0|1
            packet_size += 3    # O1 + 0|1

        else:
            raise NotSupportedError()

        return int(packet_size)

    def __initFile(self, filename):
        self.__f = open(filename, "w")
        header = "NSeq, I1, I2, O1, O2, "
        for i in range(self.__num_chs):
            ch = self.__chs[i]
            if ch == AX1 or ch == AX2:
                if i == self.__num_chs - 1:
                    header += "AX{}".format(ch)
                else:
                    header += "AX{}, ".format(ch)
            else:
                if i == self.__num_chs - 1:
                    header += "AI{}".format(ch)
                else:
                    header += "AI{}, ".format(ch)
        self.__f.write(header + "\n")

    def __writeFramesFile(self, frames):
        self.__f.write("\n".join(map(str,frames))+ "\n")


    def __closeFile(self):
        self.__f.close()


    def __changeAPI(self, api):
        if self.__num_chs and self.__num_chs != 0:
            raise DeviceNotIdleError()

        if api <= 0 or api > 3:
            raise InvalidParameterError()

        self.__api_mode = api

        api <<= 4
        api |= 0b11

        self.__send(api)

    def __checkCRC4(self, data, length):
        CRC4tab = [0, 3, 6, 5, 12, 15, 10, 9, 11, 8, 13, 14, 7, 4, 1, 2]
        crc = 0
        for i in range(length - 1):
            b = data[i]
            crc = CRC4tab[crc] ^ (b >> 4)
            crc = CRC4tab[crc] ^ (b & 0x0F)

        # CRC for last byte
        crc = CRC4tab[crc] ^ (data[-1] >> 4)
        crc = CRC4tab[crc]

        return crc == (data[ - 1] & 0x0F)

    def __send(self, command, nrOfBytes=None):
        """
        Send data
        """
        if type(command) is int:
            if command != 0:
                command = command.to_bytes(
                    int(log2(command) // 8 + 1), byteorder="little"
                )
            else:
                command = b"\x00"
        if nrOfBytes and len(command)<nrOfBytes:
            for _ in range(nrOfBytes-len(command)):
                command += b"\x00"
        # if self.__serial:
        time.sleep(0.150)
        if self.__log:
            print("{} bytes sent: ".format(len(command))+ " ".join("{:02x}".format(c) for c in command))
        if self.__socket:
            self.__socket.send(command)
        else:
            self.__serial.write(command)
        # else:
            # raise ContactingDeviceError()

    def __recv(self, nrOfBytes):
        """
        Receive data
        """
        result = None
        if self.__socket:
            result = self.__socket.recv(nrOfBytes)
        else:
            result = self.__serial.read(nrOfBytes)
        if self.__log:
            if nrOfBytes>1:
                print("{} bytes received: ".format(nrOfBytes)+ " ".join("{:02x}".format(c) for c in result))
            else:
                print("{} bytes received: {}".format(1,result.hex()))
        return result

    def __clear(self):
        """
        Clear the device buffer
        """
        if self.__socket:
            self.__socket.setblocking(False)
        else:
            self.__serial.timeout = 0

        try:
            while self.__recv(1):
                pass
        except BlockingIOError:
            pass

        if self.__socket:
            self.__socket.setblocking(True)
        else:
            self.__serial.timeout = TIMEOUT_IN_SECONDS
