from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal, List, Optional
import torch
from botorch.models import SingleTaskGP
from botorch.fit import fit_gpytorch_model
from gpytorch.mlls import ExactMarginalLogLikelihood
from botorch.acquisition import ExpectedImprovement, UpperConfidenceBound, ProbabilityOfImprovement
from botorch.optim import optimize_acqf
from fastapi import FastAPI, HTTPException

app = FastAPI()

train_x = None  # type: Optional[torch.Tensor]
train_y = None  # type: Optional[torch.Tensor]
gp_model = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
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

# Global history storage
history: List[dict] = []

class BatchResult(BaseModel):
    candidates: list[list[float]]
    scores: list[float]

# --- 맨 위 전역 변수 선언부 바로 아래에 추가 ---
@app.post("/reset")
async def reset_bayesian():
    """
    진행 중이던 Bayesian optimizer 상태를 완전 초기화합니다.
    """
    global train_x, train_y, gp_model, history

    train_x = None
    train_y = None
    gp_model = None
    history = []

    return {
        "status": "success",
        "message": "Bayesian optimizer state and history have been reset."
    }

@app.post("/submit")
def submit(result: BatchResult):
    global train_x, train_y

    # 1) candidates → 텐서 생성
    x = torch.tensor(result.candidates, dtype=torch.double)
    # 1D라면 [D] → [1, D]
    if x.ndim == 1:
        x = x.unsqueeze(0)
    # 2D여도, 3D 이상이면 에러
    if x.ndim != 2:
        raise HTTPException(
            status_code=400,
            detail=f"`candidates` must be 1D or 2D list, got ndim={x.ndim}"
        )

    # 2) scores → [N,1] 텐서 생성
    y = torch.tensor(result.scores, dtype=torch.double)
    if y.ndim == 1:
        y = y.unsqueeze(-1)
    if y.ndim != 2 or y.size(1) != 1:
        raise HTTPException(
            status_code=400,
            detail=f"`scores` must be 1D or Nx1 list, got shape={y.shape}"
        )

    # 3) 첫 입력인지 판단
    if train_x is None:
        train_x = x.clone()
        train_y = y.clone()
    else:
        # 피처 차원 일치 확인
        if x.size(1) != train_x.size(1):
            raise HTTPException(
                status_code=400,
                detail=(
                  f"Feature dimension mismatch: "
                  f"expected {train_x.size(1)}, got {x.size(1)}"
                )
            )
        train_x = torch.cat([train_x, x], dim=0)
        train_y = torch.cat([train_y, y], dim=0)

    return {
        "status": "ok",
        "total_evaluations": train_x.size(0),
        "feature_dim": train_x.size(1),
    }


@app.get("/suggest")
def suggest(batch_size: int = 4):
    global gp_model, train_x, train_y
    # 1) if first call, do Sobol init:
    if train_x.shape[0] < 8:
        # draw Sobol samples in your bounds
        new_x = draw_sobol_samples(bounds=param_bounds, n=batch_size).to(dtype=torch.double)
    else:
        # 2) fit GP, define acquisition (e.g. qNEI), call optimize
        gp_model = fit_gpytorch_model(ExactMarginalLogLikelihood(gp_model.likelihood, gp_model))
        new_x, _ = optimize_acqf(
            acq_function=qNoisyExpectedImprovement(model=gp_model, X_baseline=train_x),
            bounds=param_bounds,
            q=batch_size,
            num_restarts=10,
            raw_samples=256,
        )
    # convert to plain lists
    pts = new_x.cpu().tolist()
    return {"candidates": pts}

@app.post("/get_suggestion")
def get_suggestion(config: BOConfig):
    """
    Return next candidate based on current history and BOConfig.
    If history is empty, returns a random point.
    """
    global history
    torch.manual_seed(0)
    dim = len(config.parameters)

    # Build bounds from parameters
    bounds = torch.tensor([
        [p.min for p in config.parameters],
        [p.max for p in config.parameters],
    ], dtype=torch.double)

    # Suggest initial random
    if not history:
        next_x = torch.rand(1, dim).tolist()[0]
    else:
        # Prepare training data
        X = torch.tensor([h['x'] for h in history], dtype=torch.double)
        Y = torch.tensor([[h['score']] for h in history], dtype=torch.double)

        model = SingleTaskGP(X, Y)
        mll = ExactMarginalLogLikelihood(model.likelihood, model)
        fit_gpytorch_model(mll)

        # Select acquisition function
        if config.acquisition == "ei":
            acq = ExpectedImprovement(model, best_f=Y.max())
        elif config.acquisition == "ucb":
            acq = UpperConfidenceBound(model, beta=0.1)
        else:
            acq = ProbabilityOfImprovement(model, best_f=Y.max())

        # Optimize acquisition
        candidate, _ = optimize_acqf(
            acq_function=acq,
            bounds=bounds,
            q=1,
            num_restarts=5,
            raw_samples=20,
        )
        next_x = candidate.detach().tolist()[0]

    return {"next_x": next_x, "history": history}

@app.post("/submit_score")
def submit_score(meas: Measurement):
    """
    Append measured score to history and return updated history.
    """
    global history
    history.append({"x": meas.x, "score": meas.score})
    return {"history": history}


