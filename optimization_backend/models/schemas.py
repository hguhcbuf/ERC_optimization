from pydantic import BaseModel
from typing import List, Literal



class Objective(BaseModel):
    name: str
    method: Literal["manual", "bus 1", "bus 2"]
    direction: Literal["Minimize", "Maximize"]

class Parameter(BaseModel):
    name: str
    min: float
    max: float

class BOConfig(BaseModel):
    acquisition: Literal["ei", "ucb", "pi"]
    parameters: List[Parameter]

class Measurement(BaseModel):
    x: List[float]
    score: float

class BatchResult(BaseModel):
    candidates: List[List[float]]
    scores: List[float]

class PressureRequest(BaseModel):
    pressure: float





