import torch
from typing import Optional
from botorch.models import SingleTaskGP
from gpytorch.mlls import ExactMarginalLogLikelihood
from botorch.fit import fit_gpytorch_mll
from botorch.acquisition import ExpectedImprovement, UpperConfidenceBound, ProbabilityOfImprovement
from botorch.optim import optimize_acqf

# 글로벌 상태
train_x: Optional[torch.Tensor] = None
train_y: Optional[torch.Tensor] = None
gp_model = None
history: list[dict] = []

def reset_optimizer_state():
    global train_x, train_y, gp_model, history
    train_x = None
    train_y = None
    gp_model = None
    history = []

def add_batch_result(x, y):
    global train_x, train_y
    if train_x is None:
        train_x = x.clone()
        train_y = y.clone()
    else:
        if x.size(1) != train_x.size(1):
            raise ValueError(f"Feature dimension mismatch: expected {train_x.size(1)}, got {x.size(1)}")
        train_x = torch.cat([train_x, x], dim=0)
        train_y = torch.cat([train_y, y], dim=0)

def get_next_suggestion(config, history_data):
    torch.manual_seed(0)
    dim = len(config.parameters)
    bounds = torch.tensor([
        [p.min for p in config.parameters],
        [p.max for p in config.parameters],
    ], dtype=torch.double)

    if not history_data:
        return torch.rand(1, dim).tolist()[0]

    X = torch.tensor([h['x'] for h in history_data], dtype=torch.double)
    Y = torch.tensor([[h['score']] for h in history_data], dtype=torch.double)

    model = SingleTaskGP(X, Y)
    mll = ExactMarginalLogLikelihood(model.likelihood, model)
    fit_gpytorch_mll(mll)

    if config.acquisition == "ei":
        acq = ExpectedImprovement(model, best_f=Y.max())
    elif config.acquisition == "ucb":
        acq = UpperConfidenceBound(model, beta=0.1)
    else:
        acq = ProbabilityOfImprovement(model, best_f=Y.max())

    candidate, _ = optimize_acqf(
        acq_function=acq,
        bounds=bounds,
        q=1,
        num_restarts=5,
        raw_samples=20,
    )
    return candidate.detach().tolist()[0]
