import pyads
import time
import serial
from fastapi import HTTPException


AMS_NET_ID = '192.168.0.2.1.1'
PLC_PORT = pyads.PORT_TC3PLC1

PLC_VAR_EXTRUDE = "Temp_Motion_Exe.bExtrude"

def set_extrude(state: bool):
    plc = pyads.Connection(AMS_NET_ID, PLC_PORT)
    plc.open()
    plc.write_by_name(PLC_VAR_EXTRUDE, state, pyads.PLCTYPE_BOOL)
    plc.close()




# NordSer = serial.Serial(port='COM3', baudrate=9600, parity="N", stopbits=1, bytesize=8, timeout=2)

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
    print(f"[DEBUG] 입력된 pressure: {pressure}")

    try:
        with serial.Serial(
            port='COM4',
            baudrate=9600,
            parity="N",
            stopbits=1,
            bytesize=8,
            timeout=2
        ) as NordSer:

            NordSer.reset_input_buffer()
            NordSer.reset_output_buffer()

            NordSer.write(bytearray([bENQ]))

            if not (int.from_bytes(NordSer.read(1), "big") == bACK):
                print("[WARNING] ACK 신호 수신 실패")
                time.sleep(0.2)

            Comm1 = PacketGenerator(command='PS  ', data=format_number(pressure))
            print(f"[DEBUG] PacketGenerator 출력: {Comm1}")

            NordSer.write(bytearray(Comm1))
            time.sleep(0.2)

            response = NordSer.read_until(expected=bytes([bETX]))
            print(f"[DEBUG] 장비 응답: {response}")

            NordSer.write(bytearray([bEOT]))
            time.sleep(0.2)

    except serial.SerialException as e:
        print(f"[ERROR] 시리얼 포트 연결 실패: {e}")
        raise HTTPException(status_code=500, detail=f"시리얼 포트 연결 실패: {e}")

    
    
