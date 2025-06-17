import serial
import time
import re


class NordsonEFD:

    _bSTX = 0x02 # Start of Text
    _bETX = 0x03 # End of Text
    _bEOT = 0x04 # End of Transmission
    _bENQ = 0x05 # Enquiry
    _bACK = 0x06 # Acknowledgment
    _bNAK = 0x15 # Negative Acknowledgment

    _Success = 'A0'
    _Failed = 'A2'


    def __init__(self, port='COM4', baudrate=115200, timeout=1):

        
        self._Serial = serial.Serial(port=port, baudrate=baudrate, parity="N", stopbits=1, bytesize=8, timeout=timeout)
        self.ResetBuffer()
        self.CurrentPressure = 0.0


    @staticmethod
    def ByteArrayPrinter(func):
        def decorated(*args, **kwargs):
            output = func(*args, **kwargs)
            print(f'*** Text Packet(Hex): ***')
            for byte in output:
                print(format(byte, '02X'), end=" ")
            print()
            return output
        return decorated
    

    @staticmethod
    def ZFill4Digits(number : float,
                     ndigits: int):
        ''' Convert the input number to a string and remove the decimal point '''
        pressure = number*(10**ndigits)
        return str(round(pressure)).zfill(4)
    

    @staticmethod
    def ChecksumGen(checkBytes=bytearray()):
            checksum = (-sum(checkBytes)) & 0xFFFF
            checkStr = format(checksum, '02X')[-2:]
            checkPacket = bytearray(checkStr.encode())
            return checkPacket


    @staticmethod
    def Decoration4Communication(func):
        def decorated(*args, **kwargs):
            _self = args[0]
            _self.ResetBuffer()
            _self._Serial.write(bytearray([_self._bENQ]))
            _self._Serial.read_until(expected=bytes([_self._bACK]))
            output = func(*args, **kwargs)
            _self._Serial.write(bytearray([_self._bEOT]))
            return output
        return decorated


    def PacketDecoder(self, msg : bytes):
        if int(msg[1:3].decode(), 16) != len(msg[3:-3]):
            raise('Received message error: Packet length mismatch')
        
        if self.ChecksumGen(checkBytes=msg[1:-3]) != msg[-3:-1]:
            raise('Received message error: Checksum mismatch')

        return msg[3:-3].decode()


    # @ByteArrayPrinter
    def PacketGenerator(self, command : str='', data : str=''):
        '''STX + No. Bytes + (command) + (data) + Checksum + ETX'''

        commPack = bytearray(command.encode())
        dataPack = bytearray(data.encode())

        No_Bytes = len(commPack) + len(dataPack)
        No_Packet = bytearray(format(No_Bytes, '02X').encode())

        packet = (bytearray([self._bSTX])
                + No_Packet + commPack + dataPack
                + self.ChecksumGen(No_Packet + commPack + dataPack)
                + bytearray([self._bETX]))

        return packet
    

    def ResetBuffer(self):
        self._Serial.reset_input_buffer()
        self._Serial.reset_output_buffer()


    @Decoration4Communication
    def SetPressure(self, pressure):
        '''
        ### Input
        - pressure(kPa): 0.0 ~ 689.5
        ### Return
        - True: Successfully set.
        - False: Problem occured.
        '''
        if type(pressure) != type(float()):
            pressure = float(pressure)
        if pressure < 0 or pressure > 689.5:
            print("##################### Error #####################")
            print("### Pressure Setting Required: 0.0 ~ 689.5kPa ###")
            print("########### Automatically set to 0kPa ###########")
            print("#################################################")
            pressure = float(0)
        PressureSetPacket = self.PacketGenerator(command='PS  ',
                                                 data=self.ZFill4Digits(number=pressure,
                                                                        ndigits=1))
        self._Serial.write(bytearray(PressureSetPacket))
        respond = self._Serial.read_until(expected=bytes([self._bETX]))
        try:
            if self.PacketDecoder(respond) == self._Success:
                
                return True
            else:
                
                return False
        except:
            
            return False

    @Decoration4Communication
    def ReadPressure(self):
        ReadSetPacket = self.PacketGenerator(command='UD  ', data='C3')
        self._Serial.write(bytearray(ReadSetPacket))
        respond = self._Serial.read_until(expected=bytes([self._bETX]))
        if self.PacketDecoder(respond) == self._Failed:
            return False
        else:
            self.ResetBuffer()
        self._Serial.write(bytearray([self._bACK]))
        respond = self._Serial.read_until(expected=bytes([self._bETX]))
        data = self.PacketDecoder(respond)
        
        ccc = re.search(r'CH(\d{3})', data)
        pppp = re.search(r'PD(\d{4})', data)
        tttt = re.search(r'DT(\d{4})', data)

        pressure = float(pppp.group(1))/10
        return pressure   