

import numpy as np



def calculate_last_line_stddev(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        print("파일이 비어 있습니다.")
        return None

    # 마지막 줄
    last_line = lines[-1].strip()

    # 공백 / 탭 기준으로 분리
    data_strings = last_line.split()

    values = []

    for val in data_strings:
        try:
            f_val = float(val)

            if f_val != 0.0:
                values.append(f_val)

        except ValueError:
            continue

    if not values:
        print("유효한 데이터가 없습니다.")
        return None

    # 모집단 표준편차
    stddev = np.std(values, ddof=0)

    return -round(stddev, 5)



from pathlib import Path

GCODE_PATH = Path(r"C:\Users\Administrator\Desktop\GCodes\EGaln_line.nc")

def write_gcode(x: float, y: float, v: float, h: float, p: float):
    vel = v * 60
    profile_x = x -6.3
    profile_y = y -290.0
    final_y = y+30
    standoff = 15 + h
    gcode = f"""
R100={p:.1f}
M100
G00 X{x:.1f} Y{y:.1f} Z30
G04 F1
G00 Y{y:.1f} Z{standoff:.1f}
M10
G01 Y{final_y:.1f} Z{standoff:.1f} F{vel:.1f}
M11
G01 Y{final_y:.1f} Z30 F{vel:.1f}
G00 X{profile_x:.1f} Y{profile_y:.1f} Z30
M50
G00 X{x:.1f} Y{y:.1f} Z30



M30

"""
    GCODE_PATH.write_text(gcode, encoding="utf-8")