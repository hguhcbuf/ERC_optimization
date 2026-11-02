import socket
import time
import threading


SERVER_IP = "192.168.0.3"   # 캡처PC IP
PORT = 5000


def trigger_capture(filename):
    msg = f"CAPTURE%{filename}"  # 서버 포맷과 통일

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, PORT))
        s.sendall(msg.encode())
        s.recv(1024)

def delayed_capture(filename, delay=0.5):
    time.sleep(delay)
    trigger_capture(filename)

def schedule_capture(filename, delay=0.5):
    threading.Thread(
        target=delayed_capture,
        args=(filename, delay),
        daemon=False
    ).start()

# trigger_capture("finding v_star_trial2.png")

# run = 6
# fname = f"run_{run:03d}_Uz5_H3_rep1.png"

# schedule_capture(fname, delay = 3)


