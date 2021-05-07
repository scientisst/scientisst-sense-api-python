import bluetooth
import time
from math import log2

TIMEOUT_IN_SECONDS = 3


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

class Frame:
    digital = [0] * 4
    seq = None
    a = [0] * 8

    def toMap(self):
        return {"sequence": self.seq, "analog": self.a, "digital": self.digital}

    def toString(self):
        return str(self.toMap())

def find():
    nearby_devices = bluetooth.discover_devices(lookup_names=True)

    c = 0
    for addr, name in nearby_devices:
        if "scientisst" in name.lower():
            if c == 0:
                "Devices found:"
            c += 1
            print("{} - {}".format(addr, name))
    if c == 0:
        print("Found no devices")


class ScientISST:
    port = 1
    sock = None
    __num_chs = 0
    __api_mode = 1
    __sample_rate = None
    __chs = [None] * 8
    __f = None

    def __init__(self, address):
        self.address = address

    def connect(self):

        # Close socket if it exists
        if self.sock:
            self.disconnect()

        print("Connecting to device...")
        # Create the client socket
        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.sock.connect((self.address, self.port))
        print("Connected!")

    def version(self):
        header = "ScientISST"
        headerLen = len(header)

        cmd = b"\x07"
        self.__send(cmd)
        version = ""
        while True:
            result = self.__recv(1)
            if result:
                if len(version) >= headerLen:
                    if result == b"\x00":
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

    def start(
        self, sample_rate, channels, file_name, simulated, api=API_MODE_SCIENTISST
    ):
        if self.__num_chs != 0:
            print("Device not idle")
            return

        if api != API_MODE_SCIENTISST and api != API_MODE_JSON:
            print("Invalid parameter")
            return
        api = int(api)

        self.__sample_rate = sample_rate
        self.__num_chs = 0

        # Change API mode
        self.changeAPI(api)

        # Sample rate
        sr = 0b01000011
        sr |= self.__sample_rate << 8
        self.__send(sr)

        if not channels:  # channels is empty
            chMask = 0xFF  #  all 8 analog channels
            self.__num_chs = 8
        else:
            chMask = 0
            for ch in channels:
                self.__chs[self.__num_chs] = ch  # Fill chs vector
                if ch < 0 or ch > 8:
                    print("Invalid parameter")
                    return
                mask = 1 << (ch - 1)
                if chMask & mask:
                    print("Invalid parameter")
                    return
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

        # Open file and write header
        self.__initFile(file_name)

    def read(self, num_frames):
        num_frames = int(num_frames)
        bf = [None] * self.__packet_size

        # unsigned char buffer[500]
        # mid_frame_flag = 0
        # rapidjson::Document d
        # char memb_name[50]
        # int curr_ch
        # char* junk

        frames = [None] * num_frames

        if self.__num_chs == 0:
            print("Device not in acquisition mode")
            return

        for it in range(num_frames):
            mid_frame_flag = 0
            bf = list(self.__recv(self.__packet_size))
            if not bf:
                print(
                    "Esp stopped sending frames -> It stopped live mode on its own \n(probably because it can't handle this number of channels + sample rate)"
                )
                return

            #  if CRC check failed, try to resynchronize with the next valid frame
            while not self.__checkCRC4(bf, self.__packet_size):
                bf = bf[1:] + [None]
                #  checking with one new byte at a time
                result = self.__recv(1)
                bf[-1] = int.from_bytes(result, "big")

                if not bf[-1]:
                    return -1
                    # return int(it - frames.begin());   #  a timeout has occurred

            f = Frame()
            frames[it] = f
            if self.__api_mode == API_MODE_SCIENTISST:
                # Get seq number and IO states
                f.seq = bf[-1] >> 4
                for i in range(4):
                    f.digital[i] = (bf[-2] & (0x80 >> i)) != 0

                # Get channel values
                for i in range(self.__num_chs):
                    curr_ch = self.__chs[self.__num_chs - 1 - i]

                    # If it's an AX channel
                    if curr_ch == AX1 or curr_ch == AX2:
                        f.a[curr_ch] = (
                            int.from_bytes(bf[i : i + 4], byteorder="little") & 0xFFFFFF
                        )
                        i += 3

                    # If it's an AI channel
                    else:
                        if not mid_frame_flag:
                            f.a[curr_ch - 1] = (
                                int.from_bytes(bf[i : i + 2], byteorder="little")
                                & 0xFFF
                            )
                            i += 1
                            mid_frame_flag = 1
                        else:
                            f.a[curr_ch - 1] = (
                                int.from_bytes(bf[i : i + 2], byteorder="little") >> 4
                            )
                            i += 2
                            mid_frame_flag = 0
            # }else if(api_mode == API_MODE_JSON){
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

            self.__writeFrameFile(f)

        return frames

    def stop(self):
        if self.__num_chs == 0:
            print("Device not in acquisition mode")
            return

        cmd = b"\x00"
        self.__send(cmd)  # 0  0  0  0  0  0  0  0 - Go to idle mode

        self.__num_chs = 0
        self.__sample_rate = 0

        # Cleanup existing data in bluetooth socket
        self.__clear()

        # fclose(output_fd);
        self.__f.close()

    def __getPacketSize(self):
        packet_size = 0
        num_intern_active_chs = 0
        num_extern_active_chs = 0
        # rapidjson::Document d;
        # char value_internal_str[50];
        # char value_external_str[50];
        # char aux_str[50];
        # rapidjson::Value classname;
        # rapidjson::Value member_name(aux_str, strlen(aux_str), d.GetAllocator());
        # rapidjson::Value member_value(aux_str, strlen(aux_str), d.GetAllocator());

        for ch in self.__chs:
            if ch:
                # Add 24bit channel's contributuion to packet size
                if ch == 6 or ch == 7:
                    num_extern_active_chs += 1
                # Count 12bit channels
                else:
                    num_intern_active_chs += 1

        if self.__api_mode == API_MODE_SCIENTISST:
            packet_size = 3 * num_extern_active_chs

            # Add 12bit channel's contributuion to packet size
            if not (num_intern_active_chs % 2):  # If it's an even number
                packet_size += (num_intern_active_chs * 12) / 8
            else:
                packet_size += (
                    (num_intern_active_chs * 12) - 4
                ) / 8  # -4 because 4 bits can go in the I/0 byte
            packet_size += 2
            # for the I/Os and seq+crc bytes

        # elif api_mode == API_MODE_JSON:
        # d.SetObject();

        # Load value strings with channels' respective max values
        # sprintf(value_internal_str, "%04d", 4095);
        # sprintf(value_external_str, "%08d", 16777215);

        # for(int i = 0; i < num_chs; i++){
        # # If it's internal ch
        # if(chs[i] <= 6){
        # sprintf(aux_str, "AI%d", chs[i]);
        # member_name.SetString(aux_str, d.GetAllocator());
        # member_value.SetString(value_internal_str, d.GetAllocator());
        # d.AddMember(member_name, member_value, d.GetAllocator());

        # }else{
        # sprintf(aux_str, "AX%d", chs[i]-6);
        # member_name.SetString(aux_str, d.GetAllocator());
        # member_value.SetString(value_external_str, d.GetAllocator());
        # d.AddMember(member_name, member_value, d.GetAllocator());
        # }
        # }
        # # Add IO state json objects
        # d.AddMember("I1", "0", d.GetAllocator());
        # d.AddMember("I2", "0", d.GetAllocator());
        # d.AddMember("O1", "0", d.GetAllocator());
        # d.AddMember("O2", "0", d.GetAllocator());

        # #  3. Stringify the DOM
        # rapidjson::StringBuffer buffer;
        # rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
        # d.Accept(writer);

        # _packet_size = strlen(buffer.GetString())+1;

        return int(packet_size)

    def __initFile(self, filename):
        self.__f = open(filename, "w")
        self.__f.write("NSeq, I1, I2, O1, O2, ")
        for i in range(self.__num_chs):
            ch = int(self.__chs[i])
            if ch == AX1 or ch == AX2:
                if i == self.__num_chs - 1:
                    self.__f.write("AX{}".format(ch))
                else:
                    self.__f.write("AX{}, ".format(ch))
            else:
                if i == self.__num_chs - 1:
                    self.__f.write("AI{}".format(ch))
                else:
                    self.__f.write("AI{}, ".format(ch))
        self.__f.write("\n")

    def __writeFrameFile(self, f):
        self.__f.write(
            "{}, {}, {}, {}, {}, ".format(
                f.seq, f.digital[0], f.digital[1], f.digital[2], f.digital[3]
            )
        )

        for i in range(self.__num_chs):
            if i == self.__num_chs - 1:
                # self.__f.write("%d", esp_adc_cal_raw_to_voltage(f.a[chs[i]-1], &adc1_chars))
                self.__f.write("{}".format(f.a[self.__chs[i] - 1]))
            else:
                # self.__f.write("%d, ", esp_adc_cal_raw_to_voltage(f.a[chs[i]-1], &adc1_chars))
                self.__f.write("{}, ".format(f.a[self.__chs[i] - 1]))
        self.__f.write("\n")

    def disconnect(self):
        self.sock.close()
        self.sock = None
        print("Disconnected")

    def changeAPI(self, api):
        if self.__num_chs and self.__num_chs != 0:
            print("Device not idle")

        if api <= 0 or api > 3:
            print("Invalid API")

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

        return crc == (data[length - 1] & 0x0F)

    def __send(self, command):
        if type(command) is int:
            if command != 0:
                command = command.to_bytes(
                    int(log2(command) // 8 + 1), byteorder="little"
                )
            else:
                command = b"\x00"
        if self.sock:
            time.sleep(0.150)
            # print("{} bytes sent: ".format(len(command))+ " ".join("{:02x}".format(c) for c in command))
            self.sock.send(command)
        else:
            raise AttributeError("No device connected")

    def __recv(self, nrOfBytes):
        result = None
        self.sock.settimeout(TIMEOUT_IN_SECONDS)
        try:
            result = self.sock.recv(nrOfBytes)
            pass
        except bluetooth.btcommon.BluetoothError:
            pass
        self.sock.settimeout(None)
        return result

    def __clear(self):
        while self.__recv(1):
            pass
