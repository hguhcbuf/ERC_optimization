from PLC_communication import PLC_Var
from NordsonEFD import NordsonEFD
import time

Set_Pos_X       =	PLC_Var('PYADS.ADS_Motor.Set_Pos_X')
Set_Pos_Y       =	PLC_Var('PYADS.ADS_Motor.Set_Pos_Y')
Set_Pos_Z       =	PLC_Var('PYADS.ADS_Motor.Set_Pos_Z')
Set_Vel_X       =	PLC_Var('PYADS.ADS_Motor.Set_Vel_X')
Set_Vel_Y       =	PLC_Var('PYADS.ADS_Motor.Set_Vel_Y')
Set_Vel_Z       =	PLC_Var('PYADS.ADS_Motor.Set_Vel_Z')
Set_Enable_X    =	PLC_Var('PYADS.ADS_Motor.Set_Enable_X')
Set_Enable_Y    =	PLC_Var('PYADS.ADS_Motor.Set_Enable_Y')
Set_Enable_Z    =	PLC_Var('PYADS.ADS_Motor.Set_Enable_Z')
Set_Go          =	PLC_Var('PYADS.ADS_Motor.Set_Go')
Act_Pos_X       =	PLC_Var('PYADS.ADS_Motor.Act_Pos_X')
Act_Pos_Y       =	PLC_Var('PYADS.ADS_Motor.Act_Pos_Y')
Act_Pos_Z       =	PLC_Var('PYADS.ADS_Motor.Act_Pos_Z')
Act_Vel_X       =	PLC_Var('PYADS.ADS_Motor.Act_Vel_X')
Act_Vel_Y       =	PLC_Var('PYADS.ADS_Motor.Act_Vel_Y')
Act_Vel_Z       =	PLC_Var('PYADS.ADS_Motor.Act_Vel_Z')
Get_Enable_X    =	PLC_Var('PYADS.ADS_Motor.Get_Enable_X')
Get_Enable_Y    =	PLC_Var('PYADS.ADS_Motor.Get_Enable_Y')
Get_Enable_Z    =	PLC_Var('PYADS.ADS_Motor.Get_Enable_Z')
Get_IDLE        =	PLC_Var('PYADS.ADS_Motor.Get_IDLE')

Set_KeyenceMode =   PLC_Var('PYADS.ADS_Keyence.Set_KeyenceMode')
Force_Capture	=   PLC_Var('PYADS.ADS_Keyence.Force_Capture')

Set_ExtMode     =   PLC_Var('PYADS.ADS_Nordson.Set_ExtMode')

# inst = NordsonEFD(port='COM4', baudrate=115200, timeout=1)
# inst.SetPressure(20)
# print(inst.ReadPressure())

Force_Capture.write(True)


Set_Enable_X.write(True)
Set_Enable_Y.write(True)
Set_Enable_Z.write(True)

Set_Pos_Y.write(10)
Set_Vel_Y.write(500)
Set_ExtMode.write(0)
Set_KeyenceMode.write(2)

Set_Go.write(True)

########################################

while True:
    if not Get_IDLE.read():
        Set_Enable_X.write(True)
        Set_Enable_Y.write(True)
        Set_Enable_Z.write(True)

        Set_Pos_Y.write(500)
        Set_Vel_Y.write(300)

        Set_ExtMode.write(2)
        break

while True:
    if Get_IDLE.read():
        Set_Go.write(True)
        break
    else:
        time.sleep(0.001)




while True:
    if not Get_IDLE.read():
        Set_Enable_X.write(True)
        Set_Enable_Y.write(True)
        Set_Enable_Z.write(True)

        Set_Pos_Y.write(450)
        Set_Vel_Y.write(50)

        Set_ExtMode.write(1)
        break

while True:
    if Get_IDLE.read():
        Set_Go.write(True)
        break
    else:
        time.sleep(0.001)