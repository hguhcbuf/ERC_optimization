from pathlib import Path

GCODE_PATH = Path(r"C:\Users\Administrator\Desktop\GCodes\pillar.nc")

def write_pillar_gcode(x: float, y: float, v: float, h: float):
    vel = v * 680
    init_height = 13.02
    final_height = init_height + h*0.25
    gcode = f"""
N10 G90

N30 G00 X{x:.3f} Y{y:.3f} Z30.000
N40 G01 Z{init_height:.3f} F1200

N51 M10
N60 G04 F1

N70 G01 Z{final_height:.3f} F{vel:.3f}

N80 M11

N90 G01 Z30.000 F1200

N100 G91
N110 G00 Y-307.90 X-6.600
N120 G90

N130 M50

N140 M30

"""
    GCODE_PATH.write_text(gcode, encoding="utf-8")


GCODE_PATH2 = Path(r"C:\Users\Administrator\Desktop\GCodes\pillar_array.nc")


def write_pillar_array_gcode(
    x0: float,   # 시작 X
    y0: float,   # 시작 Y
    v: float,    # v*
    h: float,    # h*
    n: int,      # row 개수 (Y방향)
    m: int,      # column 개수 (X방향)
    d: float     # 간격 (mm)
):
    vel = v * 620
    init_height = 10.00
    final_height = init_height + h * 0.25

    gcode = ""

    # ===== 헤더 =====
    gcode += """
N10 G90
"""

    line = 20  # 라인 번호 시작

    for i in range(n):        # row (Y)
        for j in range(m):    # col (X)

            x = x0 + j * d
            y = y0 + i * d

            gcode += f"""
N{line}   G00 X{x:.3f} Y{y:.3f} Z30.000
N{line+10} G01 Z{init_height:.3f} F1200

N{line+20} M10
N{line+30} G04 F1

N{line+40} G01 Z{final_height:.3f} F{vel:.3f}

N{line+50} M11

N{line+60} G01 Z30.000 F1200
"""

            line += 100   # 라인 번호 증가

    # ===== 종료 =====
    gcode += f"""
N{line}   M50
N{line+10} M30
"""
    print('aaa')
    GCODE_PATH2.write_text(gcode, encoding="utf-8")

    print(f"Saved: {GCODE_PATH2}")




GCODE_PATH3 = Path(r"C:\Users\Administrator\Desktop\GCodes\pillar_no_scan.nc")

def write_pillarNoScan_gcode(x: float, y: float, v: float, h: float):
    vel = v * 680
    init_height = 13.02
    final_height = init_height + h*0.25
    gcode = f"""
N10 G90

N30 G01 X{x:.3f} Y{y:.3f} Z35.000 F600
N40 G01 Z{init_height:.3f} F1200

N51 M10
N60 G04 F2

N70 G01 Z{final_height:.3f} F{vel:.3f}

N80 M11

N90 G01 Z35.000 F1200

N140 M30

"""
    GCODE_PATH3.write_text(gcode, encoding="utf-8")