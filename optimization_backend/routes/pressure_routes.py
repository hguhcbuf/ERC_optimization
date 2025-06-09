from fastapi import APIRouter
from services.pressure_service import set_extrude
from services.pressure_service import PressureApply
from models.schemas import PressureRequest


router = APIRouter()

@router.post("/extrude/on")
async def extrude_on():
    set_extrude(True)
    return {"message": "Extrude ON"}

@router.post("/extrude/off")
async def extrude_off():
    set_extrude(False)
    return {"message": "Extrude OFF"}

@router.post("/apply")
async def apply_pressure(request: PressureRequest):
    rounded_pressure = round(request.pressure, 2)
    PressureApply(rounded_pressure)
    return {"message": f"압력 {rounded_pressure} 적용 완료"}
