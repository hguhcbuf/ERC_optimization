import serial

NordSer = serial.Serial(port='COM3', baudrate=9600, parity="N", stopbits=1, bytesize=8, timeout=None)









bSTX = 0x02 # Start of Text
bETX = 0x03 # End of Text
bEOT = 0x04 # End of Transmission
bENQ = 0x05 # Enquiry
bACK = 0x06 # Acknowledgment
bNAK = 0x15 # Negative Acknowledgment




def Command2Packet(command=bytearray(), data=bytearray()):
    '''STX + No. Bytes + (command) + space space + (data) + Checksum + ETX'''
    

    
    packet = bytearray()
    packet = packet + bytearray([bSTX])





    return packet

# Space, Number(0~9), A~Z is same as ord().

# a = bytes([0xa110])
# print(int.from_bytes(a,"big"))
NordSer.reset_input_buffer()
NordSer.reset_output_buffer()






NordSer.write(bytearray([bENQ]))
if (int.from_bytes(NordSer.read(1),"big") == bACK):
    sendStr = bytearray([bSTX])
    sendStr = sendStr + bytearray(b'05ED  7')
    sendStr = sendStr + bytearray([bETX])
    NordSer.write(sendStr)
    respond = NordSer.read_until(expected=bytes([bETX]))
    print(respond.hex())
    


NordSer.write(bytearray([bEOT]))

# sendList = []
# sendList.extend([bSTX])

# RXList = bytearray()
# RXList = RXList + bytearray([ord('B')])
# RXList = RXList + bytearray(b'A')
# # RXList = bytearray([bSTX])
# print(hex(RXList[0]))


# sendStr = bytearray()



# a = bytearray(b'AA')

# print(hex(int.from_bytes(bytearray(b'AA'),"big")))
# print(respo)



# NordSer.write()
# print(NordSer.read(300).hex())












# def Num2Bin(number):
#     if type(number) != 'int':
#         print(f'Number has to be integer.')
#         return 0
#     elif number > 9 or number < 0:
#         print(f'Number has to be in range of 0 ~ 9.')
#         return 0
#     else:
#         return 0b0011_0000 + number
    

# print(ord(" "))