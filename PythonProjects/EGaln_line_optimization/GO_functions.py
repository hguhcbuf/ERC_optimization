"""Profiler measurement and capture-PC communication helpers."""
import math
import socket

SERVER_IP = "192.168.0.3"
PORT = 5000


def trigger_capture(filename, server_ip=SERVER_IP, port=PORT, timeout=30.0):
    """Send CAPTURE%filename and block until the server sends a reply.

    Pass a complete image filename (BO supplies a unique .png filename).
    A reply acknowledges the request; whether it means the image is fully
    saved depends on the server. No automatic retry (avoids duplicate capture).
    """
    if not filename or any(c in filename for c in ("%", "\r", "\n", "\x00")):
        raise ValueError("Invalid capture filename.")
    msg = f"CAPTURE%{filename}"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(timeout)
        connection.connect((server_ip, port))
        connection.sendall(msg.encode("utf-8"))
        reply = connection.recv(1024)
    if not reply:
        raise RuntimeError("Capture server closed the connection without a reply.")
    response = reply.decode("utf-8", errors="replace").strip()
    if response.upper().startswith(("ERROR", "ERR", "FAIL", "NACK")):
        raise RuntimeError(f"Capture server reported failure: {response}")
    return response


def calculate_surface_area(file_path, profile_spacing_um=5.0,
                           profile_length_unit="mm", expected_profiles=1000, min_profile_length_mm=5.0):
    """Return measured area in mm^2 from the last nonempty profiler row.

    Accept tab-delimited TXT and comma-delimited CSV rows.
    User-confirmed input: '+'-prefixed profile lengths are in mm.
    S = sum(profile_lengths_mm) * (profile_spacing_um / 1000).
    For 1000 profiles at 5 um spacing, clamp each length to >= 5 mm.
    This makes the minimum area 25 mm^2; missing profiles remain invalid.
    No substrate subtraction is performed; this integrates the exported
    profile lengths as supplied by the profiler.

    Return None for a missing/incomplete/invalid row (the BO loop retries).
    Configuration errors raise ValueError. Set expected_profiles=None only
    if variable-length complete rows are intentionally exported.
    """
    if not math.isfinite(profile_spacing_um) or profile_spacing_um <= 0:
        raise ValueError("profile_spacing_um must be finite and > 0.")
    if not math.isfinite(min_profile_length_mm) or min_profile_length_mm < 0:
        raise ValueError("min_profile_length_mm must be finite and >= 0.")
    scales = {"mm": 1.0, "um": 0.001}
    if profile_length_unit not in scales:
        raise ValueError("profile_length_unit must be 'mm' or 'um'.")
    if expected_profiles is not None and expected_profiles <= 0:
        raise ValueError("expected_profiles must be positive or None.")
    with open(file_path, "r", encoding="utf-8-sig") as stream:
        lines = [line.strip() for line in stream if line.strip()]
    if not lines:
        return None
    values = []
    # Keyence exports may use tabs (TXT) or commas (CSV).
    for token in lines[-1].replace("\t", ",").split(","):
        token = token.strip()
        if not token.startswith("+"):
            continue
        try:
            value = float(token)
        except ValueError:
            return None
        if not math.isfinite(value) or value < 0:
            return None
        values.append(max(value * scales[profile_length_unit], min_profile_length_mm))
    if not values or (expected_profiles is not None and len(values) != expected_profiles):
        return None
    area_mm2 = math.fsum(values) * profile_spacing_um / 1000.0
    return round(area_mm2, 5)
