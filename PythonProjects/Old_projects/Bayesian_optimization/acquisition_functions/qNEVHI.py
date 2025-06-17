# qei_hartmann6_fix.py  ─ 최소화 → 최대화로 변환
import torch
from torch import Size
from botorch.test_functions import Hartmann
from botorch.models import SingleTaskGP
from botorch.models.transforms import Normalize, Standardize
from botorch.acquisition.monte_carlo import qExpectedImprovement
from botorch.optim import optimize_acqf
from botorch.sampling.normal import SobolQMCNormalSampler
from botorch.fit import fit_gpytorch_model
from gpytorch.mlls import ExactMarginalLogLikelihood
from botorch.utils.sampling import draw_sobol_samples

dtype  = torch.double
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 1) Hartmann6  (원래는 "작을수록" 좋음)
hartmann6 = Hartmann(dim=6).to(dtype=dtype, device=device)

# 2) 검색 범위 [0,1]^6
bounds = torch.stack(
    [torch.zeros(6, dtype=dtype), torch.ones(6, dtype=dtype)]
).to(device)

# 3) 초기 설계
n_init = 8
X = (
    draw_sobol_samples(bounds=bounds, n=1, q=n_init)
    .squeeze(0)
    .to(dtype=dtype, device=device)
)

# **부호 반전!  (최소화 → 최대화)**
Y = (-hartmann6(X)).unsqueeze(-1)          # “큰 값이 좋다” 로 변환

def fit_model(X, Y):
    model = SingleTaskGP(
        X, Y,
        input_transform   = Normalize(d=6),
        outcome_transform = Standardize(m=1),
    )
    fit_gpytorch_model(ExactMarginalLogLikelihood(model.likelihood, model))
    return model

q, n_iter, mc_samples = 4, 10, 512
sampler = SobolQMCNormalSampler(sample_shape=Size([mc_samples]))

for i in range(1, n_iter + 1):
    model = fit_model(X, Y)

    # **best_f = Y.max()  ←  이제 “큰 값” 기준**
    acq = qExpectedImprovement(model, best_f=Y.max().item(), sampler=sampler)

    # 후보 탐색
    cand, _ = optimize_acqf(
        acq_function = acq,
        bounds       = bounds,
        q            = q,
        num_restarts = 20,
        raw_samples  = 1024,
        options      = {"batch_limit": 5, "maxiter": 200},
    )

    # **부호 반전 유지**
    Y_new = (-hartmann6(cand)).unsqueeze(-1)
    X, Y  = torch.cat([X, cand]), torch.cat([Y, Y_new])

    # 사람이 보기 좋게 “실제 최소값” 도 출력
    best_true = (-Y).min().item()     # 부호 다시 돌려서 최소값
    print(f"[{i:02}]  best f(x) so far = {best_true:.4f}")


