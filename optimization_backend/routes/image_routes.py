from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path, PurePath
import os, datetime as dt


router = APIRouter()

IMAGE_DIR = Path(r"C:\FTP\Keyence\lj-s\image\SD2_001\image_250615")

@router.get("/last_image")
def get_latest_image():
    debug_dir()
    bmp_files = sorted(IMAGE_DIR.glob("*.bmp"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not bmp_files:
        return {"error": "No image found."}

    latest_file = bmp_files[0]
    return FileResponse(latest_file, media_type="image/bmp", filename=latest_file.name)





def debug_dir():
    print("\n=== 디버그", dt.datetime.now(), "===")
    print("폴더 존재? :", IMAGE_DIR.exists())
    print("읽기 권한? :", os.access(IMAGE_DIR, os.R_OK))
    print("파일 개수(bmp) :", len(list(IMAGE_DIR.glob('*.bmp'))))
    print("파일 개수(BMP) :", len(list(IMAGE_DIR.glob('*.BMP'))))
    print("최근 5개 ↓")
    for p in sorted(IMAGE_DIR.glob('*.bmp'), key=lambda x:x.name)[-5:]:
        print("  ", p.name, p.stat().st_size, "bytes")
