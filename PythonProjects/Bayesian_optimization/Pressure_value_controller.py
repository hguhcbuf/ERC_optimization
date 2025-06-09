import serial
import time

NordSer = serial.Serial(port='COM4', baudrate=9600, parity="N", stopbits=1, bytesize=8, timeout=2)

bSTX = 0x02 # Start of Text
bETX = 0x03 # End of Text
bEOT = 0x04 # End of Transmission
bENQ = 0x05 # Enquiry
bACK = 0x06 # Acknowledgment
bNAK = 0x15 # Negative Acknowledgment


def ByteArrayPrinter(func):
    def decorated(*args, **kwargs):
        output = func(*args, **kwargs)
        print(f'*** Text Packet(Hex): ***')
        for byte in output:
            print(format(byte, '02X'), end=" ")
        print()
        return output
    return decorated


# @ByteArrayPrinter
def PacketGenerator(command='', data=''):
    '''STX + No. Bytes + (command) + (data) + Checksum + ETX'''

    def ChecksumGen(checkBytes=bytearray()):
        checksum = (-sum(checkBytes)) & 0xFFFF
        checkStr = format(checksum, '02X')[-2:]
        checkPacket = bytearray(checkStr.encode())
        return checkPacket
    
    commPack = bytearray(command.encode())
    dataPack = bytearray(data.encode())

    No_Bytes = len(commPack) + len(dataPack)
    No_Packet = bytearray(format(No_Bytes, '02X').encode())

    packet = (bytearray([bSTX])
              + No_Packet + commPack + dataPack
              + ChecksumGen(No_Packet + commPack + dataPack)
              + bytearray([bETX]))

    return packet

    
def format_number(num):
    # Convert the number to a string and remove the decimal point
    num_str = str(num).replace('.', '')
    # Pad the string with leading zeros until it has 4 characters
    return num_str.zfill(4)




def PressureApply(pressure):
    print(f"[DEBUG] 입력된 pressure: {pressure}")  # pressure 값 출력

    NordSer.reset_input_buffer()
    NordSer.reset_output_buffer()

    NordSer.write(bytearray([bENQ]))

    if not (int.from_bytes(NordSer.read(1), "big") == bACK):
        time.sleep(0.2)

    Comm1 = PacketGenerator(command='PS  ', data=format_number(pressure))
    print(f"[DEBUG] PacketGenerator 출력: {Comm1}")  # 패킷 내용 출력

    NordSer.write(bytearray(Comm1))
    time.sleep(0.2)

    response = NordSer.read_until(expected=bytes([bETX]))
    print(f"[DEBUG] 장비 응답: {response}")  # 응답 출력

    NordSer.write(bytearray([bEOT]))
    time.sleep(0.2)

    
    

