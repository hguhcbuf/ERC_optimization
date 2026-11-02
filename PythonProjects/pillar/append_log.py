
from datetime import datetime
import time
import os


def append_log(file_path, info_dict, retries=200, sleep_s=0.05):

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    line = " | ".join(f"{k}={v}" for k, v in info_dict.items())

    text = f"[{ts}] {line}\n\n"

    last_err = None

    for _ in range(retries):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "a", encoding="utf-8") as f:
                f.write(text)

            return  # 성공하면 끝

        except PermissionError as e:
            last_err = e
            time.sleep(sleep_s)

    # 그래도 실패하면 그냥 에러 띄움
    raise last_err



def wait_file_stable(path, wait=0.5, retry=10):
    last = -1

    for _ in range(retry):
        try:
            size = os.path.getsize(path)
        except:
            size = -1

        if size == last and size > 0:
            return True

        last = size
        time.sleep(wait)

    return False



def wait_file_grows(file_path: str, prev_size: int, timeout_s: float = 10.0, poll_s: float = 0.05) -> int:
    """
    Wait until file size becomes larger than prev_size.
    Returns new size.
    """
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            sz = os.path.getsize(file_path)
            if sz > prev_size:
                return sz
        except FileNotFoundError:
            pass
        time.sleep(poll_s)
    return os.path.getsize(file_path) if os.path.exists(file_path) else prev_size
