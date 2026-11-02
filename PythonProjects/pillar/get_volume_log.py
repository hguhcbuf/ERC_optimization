import re

def read_latest_volume(file_path: str) -> float:
    # 파일 전체를 읽고(크면 나중에 최적화 가능), 맨 뒤에서 분석
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()

    # 1) 맨 아래에서 위로 올라가며, 마지막 로그 라인([YYYY-...]) 위치 찾기
    last_log_idx = None
    for i in range(len(lines) - 1, -1, -1):
        s = lines[i].strip()
        if s.startswith("[") and "]" in s:
            last_log_idx = i
            break
    if last_log_idx is None:
        raise RuntimeError("No log line found at end of file.")

    # 2) last_log_idx 위쪽(데이터 영역)에서 '+000...' 형태 숫자 3개(헤더)를 찾는다.
    #    보통 헤더는 3줄 연속으로 나오므로, 위로 올라가며 '+숫자,' 라인만 수집.
    num_pat = re.compile(r"^[+ -]?\d+(?:\.\d+)?[,]*$")

    header_nums = []
    for j in range(last_log_idx - 1, -1, -1):
        s = lines[j].strip()

        # 빈 줄/로그 라인 만나면 중단 (이전 블록으로 넘어가는 걸 막음)
        if not s:
            # 빈 줄은 스킵하되, 헤더를 이미 모았으면 멈추는 게 안전
            if header_nums:
                break
            continue
        if s.startswith("["):
            break

        # "+000000000.091," 같은 형태에서 쉼표 제거 후 숫자만 검사
        s2 = s.replace(",", "").strip()
        if num_pat.match(s2):
            # 숫자 후보
            try:
                header_nums.append(float(s2))
            except ValueError:
                pass

            # 헤더는 보통 3개면 충분. (뒤에서부터 모으니까 역순)
            if len(header_nums) >= 3:
                break
        else:
            # 데이터 배열(+00000.007,+00000.007,...) 같은 줄은 통째로 숫자line이 아니라서 무시됨
            continue

    if len(header_nums) < 2:
        raise RuntimeError(f"Header numbers not found (found {len(header_nums)}).")

    # 뒤에서부터 모았으니 역순으로 뒤집으면 [첫번째, 두번째, 세번째]가 됨
    header_nums = list(reversed(header_nums))

    # 너가 원하는 "부피" = 두번째 값
    return header_nums[1]


