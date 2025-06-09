import serial
import time

NordSer = serial.Serial(port='COM3', baudrate=9600, parity="N", stopbits=1, bytesize=8, timeout=None)

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


# temp = PacketGenerator(command='A2')

for i in range(10):
    NordSer.reset_input_buffer()
    NordSer.reset_output_buffer()

NordSer.write(bytearray([bEOT]))

# while True:
#     if (int.from_bytes(NordSer.read(1),"big") == bACK):
#         break
#     else:
#         time.sleep(0.5)



def format_number(num):
    # Convert the number to a string and remove the decimal point
    num_str = str(num).replace('.', '')
    # Pad the string with leading zeros until it has 4 characters
    return num_str.zfill(4)