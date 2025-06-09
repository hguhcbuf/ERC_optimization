from fastapi import APIRouter, HTTPException
import torch
from models.schemas import BatchResult, BOConfig, Measurement
from services import bo_service

router = APIRouter()

@router.post("/reset")
async def reset_bayesian():
    bo_service.reset_optimizer_state()
    return {"status": "success", "message": "Bayesian optimizer state and history have been reset."}

@router.post("/submit")
def submit(result: BatchResult):
    x = torch.tensor(result.candidates, dtype=torch.double)
    if x.ndim == 1:
        x = x.unsqueeze(0)
    if x.ndim != 2:
        raise HTTPException(status_code=400, detail=f"`candidates` must be 1D or 2D, got ndim={x.ndim}")

    y = torch.tensor(result.scores, dtype=torch.double)
    if y.ndim == 1:
        y = y.unsqueeze(-1)
    if y.ndim != 2 or y.size(1) != 1:
        raise HTTPException(status_code=400, detail=f"`scores` must be 1D or Nx1, got shape={y.shape}")

    try:
        bo_service.add_batch_result(x, y)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "ok", "total_evaluations": bo_service.train_x.size(0), "feature_dim": bo_service.train_x.size(1)}

@router.post("/get_suggestion")
def get_suggestion(config: BOConfig):
    next_x = bo_service.get_next_suggestion(config, bo_service.history)
    return {"next_x": next_x, "history": bo_service.history}

@router.post("/submit_score")
def submit_score(meas: Measurement):
    bo_service.history.append({"x": meas.x, "score": meas.score})
    return {"history": bo_service.history}
