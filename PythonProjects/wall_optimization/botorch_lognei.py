# bo_lognei_latest.py
import os, sys, csv, json, time
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional

import torch
from torch import Tensor

# ---- BoTorch / GPyTorch ----
from botorch.models import SingleTaskGP
from botorch.models.transforms import Standardize, Normalize
from botorch.fit import fit_gpytorch_mll
from gpytorch.mlls import ExactMarginalLogLikelihood

from botorch.acquisition.monte_carlo import qUpperConfidenceBound
from botorch.acquisition.logei import qLogNoisyExpectedImprovement
from botorch.sampling.normal import SobolQMCNormalSampler
from botorch.optim import optimize_acqf

from Calculate_score import calculate_score_3sigma
from print_and_scan import print_and_scan
from NordsonEFD    import NordsonEFD

# =========================
# User Config (EDIT HERE)
# =========================
SEED = 123
MAX_ITERS = 20
N_RANDOM = 5
N_UCB = 5
UCB_BETA = 0.25
OBJECTIVE_SENSE = "min"
LOG_CSV = r"PythonProjects\wall_optimization\bo_log.csv"
LOG_PROFILE = r"C:\FTP\Keyence\lj-s\result\SD1_006\250829_104449.txt"
total_height = 0.7
inst = NordsonEFD(port="COM5", baudrate=115200, timeout=1)

# 파라미터 범위
PBONDS: Dict[str, Tuple[float, float]] = {
    "pressure"     : (150.0, 300.0),
    "velocity"     : (15.0, 30.0),
    "wall_spacing" : (0.36, 0.6),
    "number_of_layers": (2.5, 6.5),
}

# =========================
# Helpers
# =========================
torch.manual_seed(SEED)
tkwargs = {"dtype": torch.double, "device": "cpu"}

PARAMS = list(PBONDS.keys())
LB = torch.tensor([PBONDS[p][0] for p in PARAMS], **tkwargs)
UB = torch.tensor([PBONDS[p][1] for p in PARAMS], **tkwargs)
BOUNDS = torch.stack([LB, UB])
D = len(PARAMS)

def _json_dumps_safe(obj) -> str:
    try:
        from numpy import ndarray
        if isinstance(obj, Tensor):
            obj = obj.detach().cpu().tolist()
        elif isinstance(obj, ndarray):
            obj = obj.tolist()
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        try:
            return json.dumps(str(obj), ensure_ascii=False)
        except Exception:
            return ""

def ensure_csv(path: str):
    """Create CSV with header if missing (프로파일 컬럼 추가)."""
    if not Path(path).exists():
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            header = ["iter", "timestamp"] + PARAMS + [
                "objective_raw", "objective_for_BO", "acquisition",
                "profile_perpendicular", "profile_parallel",
            ]
            w.writerow(header)

def log_row(path: str, iteration: int, x: Tensor, y_raw: float, y_bo: float,
            acq_name: str, profile_perpendicular, profile_parallel):
    """Append one row to CSV (프로파일은 JSON 문자열로 저장)."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    x_list = [float(v) for v in x.view(-1).tolist()]
    row = [iteration, ts] + x_list + [
        float(y_raw), float(y_bo), acq_name,
        _json_dumps_safe(profile_perpendicular),
        _json_dumps_safe(profile_parallel),
    ]
    with open(path, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)

def sample_random(n: int = 1) -> Tensor:
    u = torch.rand(n, D, **tkwargs)
    return LB + (UB - LB) * u

def y_for_bo(y_raw: float) -> float:
    if OBJECTIVE_SENSE.lower().startswith("min"):
        return -float(y_raw)
    return float(y_raw)

def fit_model(train_X: Tensor, train_Y: Tensor) -> SingleTaskGP:
    model = SingleTaskGP(
        train_X,
        train_Y,
        input_transform=Normalize(d=D),
        outcome_transform=Standardize(m=1),
    )
    mll = ExactMarginalLogLikelihood(model.likelihood, model)
    fit_gpytorch_mll(mll)
    return model

def next_via_ucb(model: SingleTaskGP, q: int = 1) -> Tensor:
    sampler = SobolQMCNormalSampler(sample_shape=torch.Size([512]))
    acq = qUpperConfidenceBound(model, beta=UCB_BETA, sampler=sampler)
    cand, _ = optimize_acqf(
        acq_function=acq, bounds=BOUNDS, q=q,
        num_restarts=10, raw_samples=256,
        options={"batch_limit": 5, "maxiter": 200},
    )
    return cand.detach()

def next_via_lognei(model: SingleTaskGP, train_X: Tensor, train_Y: Tensor, q: int = 1) -> Tensor:
    sampler = SobolQMCNormalSampler(sample_shape=torch.Size([1024]))
    acq = qLogNoisyExpectedImprovement(model=model, X_baseline=train_X, sampler=sampler)
    cand, _ = optimize_acqf(
        acq_function=acq, bounds=BOUNDS, q=q,
        num_restarts=15, raw_samples=256,
        options={"batch_limit": 5, "maxiter": 200},
    )
    return cand.detach()

def tensorize_logs(path: str) -> Tuple[Optional[Tensor], Optional[Tensor]]:
    if not Path(path).exists():
        return None, None
    import pandas as pd
    df = pd.read_csv(path)
    if df.empty:
        return None, None
    X = torch.tensor(df[PARAMS].values, **tkwargs)
    Y_bo = torch.tensor(df["objective_for_BO"].values.reshape(-1, 1), **tkwargs)
    return X, Y_bo

def main():
    ensure_csv(LOG_CSV)

    # Warm-start
    X_all, Y_all = tensorize_logs(LOG_CSV)
    if X_all is None:
        X_all = torch.empty(0, D, **tkwargs)
        Y_all = torch.empty(0, 1, **tkwargs)
        iter_start = 1
    else:
        iter_start = int(X_all.shape[0]) + 1
        print(f"✅ Resuming from {LOG_CSV}: {iter_start-1} rows loaded.")

    # BO Loop
    for it in range(iter_start, MAX_ITERS + 1):
        if it <= N_RANDOM:
            acq_name = "RANDOM"
            x_next = sample_random(1).squeeze(0)
        else:
            if X_all.shape[0] < 2:
                x_next = sample_random(1).squeeze(0)
                acq_name = "RANDOM"
            else:
                try:
                    model = fit_model(X_all, Y_all)
                except Exception as e:
                    print(f"⚠️ GP fit failed ({e}). Fallback to RANDOM.")
                    x_next = sample_random(1).squeeze(0)
                    acq_name = "RANDOM"
                else:
                    if it <= N_RANDOM + N_UCB:
                        acq_name = f"qUCB(beta={UCB_BETA})"
                        x_next = next_via_ucb(model).squeeze(0)
                    else:
                        acq_name = "qLogNEI"
                        x_next = next_via_lognei(model, X_all, Y_all).squeeze(0)

        # ===== Evaluate (print & scan) =====
        param_values = {name: float(val) for name, val in zip(PARAMS, x_next.tolist())}
        pressure         = round(param_values["pressure"], 3)
        velocity         = round(param_values["velocity"], 3)
        wall_spacing     = round(param_values["wall_spacing"], 3)
        number_of_layers = max(1, round(param_values["number_of_layers"]))
        layer_step = round((total_height - 0.1) / number_of_layers, 3)

        try:
            inst.SetPressure(pressure)
        except Exception as e:
            print(f"⚠️ inst.SetPressure 실패: {e}")

        try:
            print_and_scan(
                it, spacing=wall_spacing, origin_z=13,
                layer_step=layer_step, n_layers=number_of_layers,
                move_x=20, move_y=320, speed=velocity,
            )
        except Exception as e:
            print(f"⚠️ print_and_scan 실패(건너뜀): {e}")

        time.sleep(7)

        y_raw, profile_perpendicular, profile_parallel = calculate_score_3sigma(LOG_PROFILE)
        y_bo = y_for_bo(y_raw)

        # Update data
        X_all = torch.cat([X_all, x_next.view(1, -1)], dim=0)
        Y_all = torch.cat([Y_all, torch.tensor([[y_bo]], **tkwargs)], dim=0)

        # Log to CSV (프로파일 포함)
        log_row(LOG_CSV, it, x_next, y_raw, y_bo, acq_name,
                profile_perpendicular, profile_parallel)

        print(f"📎 Logged iter {it} ({acq_name}) → raw={y_raw:.6g}  for_BO={y_bo:.6g}")

    print("\n🎉 BO finished.")
    print(f"Log saved to: {Path(LOG_CSV).resolve()}")

try:
    main()
except KeyboardInterrupt:
    print("\nInterrupted by user.")
    sys.exit(0)
