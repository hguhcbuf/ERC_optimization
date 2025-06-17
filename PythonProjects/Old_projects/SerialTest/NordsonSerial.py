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


# temp = PacketGenerator(command='A2')

for i in range(10):
    NotImplemented
    # print(int.from_bytes(NordSer.read(1),"big"))

NordSer.reset_input_buffer()
NordSer.reset_output_buffer()


NordSer.write(bytearray([bENQ]))

# while True:
#     if (int.from_bytes(NordSer.read(1),"big") == bACK):
#         # print(int.from_bytes(NordSer.read(1),"big"))
#         break
#     else:
#         time.sleep(0.5)
#         print('a')



def format_number(num):
    # Convert the number to a string and remove the decimal point
    num_str = str(num).replace('.', '')
    # Pad the string with leading zeros until it has 4 characters
    return num_str.zfill(4)


pressure = input("Printing Pressure (kPa): ")

# Comm1 = PacketGenerator(command='PS  ',data='0230')

Comm1 = PacketGenerator(command='PS  ',data=format_number(pressure))


NordSer.write(bytearray(Comm1))
time.sleep(0.5)
# for i in range(10):
#     t = int.from_bytes(NordSer.read(1),"big")
#     print(t)
respond = NordSer.read_until(expected=bytes([bETX]))
time.sleep(0.5)
# while True:
#     NordSer.write(bytearray(Comm1))
#     respond = NordSer.read_until(expected=bytes([bETX]))
#     print(respond)
#     if (int.from_bytes(NordSer.read(1),"big") == bACK):
#         break
#     else:
#         time.sleep(1)

NordSer.write(bytearray([bEOT]))
time.sleep(0.5)
print("Pressure set.")

# a = '02'
# str_No_Bytes = format(20, '02X')
# print(str_No_Bytes)

# print(hex(0x0000-0x0030-0x0038-0x0050-0x00539
#           -0x0020-0x0020-0x0030-0x0035-0x0030-0x0030))
# print(bytearray(a.encode()))
# print(ord(bytearray([0b1010]).decode()))

# temp = [0x0030,0x0038,0x0050,0x0053,0x0020,0x0020,0x0030,0x0035,0x0030,0x0030]
# checksum = (-sum(temp)) & 0xFFFF
# sss = format(checksum, 'X')[-2:]
# print(bytearray(sss.encode()))



# temp = bytearray(b'AaBb')
# num=0
# for b in temp:
#     print(b)
#     num = num + b
# print(num)
# print(sum(temp))