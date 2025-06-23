from fastapi import APIRouter
from models.schemas import PressureRequest
from services.plc_service import run_path


router = APIRouter()

@router.post("/home")
async def move_to_home_position():
    path_points_home = [
            ( 100,  390,  90, 30.0, 30.0, 20.0,  0, 0),
    ]
    run_path(path_points_home)
    return {"message": "Extrude OFF"}

@router.post("/origin")
async def set_origin():
    path_points_origin = [
            ( 100,  390,  15, 30.0, 30.0, 20.0,  0, 0),
    ]
    run_path(path_points_origin)
    return {"message": "Extrude OFF"}
