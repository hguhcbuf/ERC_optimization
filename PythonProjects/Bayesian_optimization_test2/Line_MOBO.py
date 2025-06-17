# mobo_qnehvi.py  ──────────────────────────────────────────────
import os, time, torch
from botorch.models import SingleTaskGP, ModelListGP
from botorch.models.transforms import Normalize, Standardize
from botorch.utils.transforms import normalize, unnormalize
from botorch.utils.sampling import draw_sobol_samples
from botorch.acquisition.multi_objective.logei import qLogNoisyExpectedHypervolumeImprovement
from botorch.optim import optimize_acqf
from botorch.sampling.normal import SobolQMCNormalSampler
from gpytorch.mlls.sum_marginal_log_likelihood import SumMarginalLogLikelihood
from botorch.fit import fit_gpytorch_mll

# ─── 사용자 코드 (장비·평가) ────────────────────────────────────
from Line_printing import print_line_by_iter
from NordsonEFD    import NordsonEFD
from Calculate_score import calculate_last_line_stddev     # ← 두 값 반환!

FILE_PATH = r"C:\FTP\Keyence\lj-s\result\SD2_001\250617_034122.txt"
LOG_DIR   = r"C:\Users\Administrator\Documents\JH\optimization_logs"
os.makedirs(LOG_DIR, exist_ok=True)

inst      = NordsonEFD(port="COM4", baudrate=115200, timeout=1)
ORIGIN_Z  = 15

# ─── torch 기본 설정 ─────────────────────────────────────────
tkwargs = dict(
    dtype   = torch.double,
    device  = torch.device("cuda" if torch.cuda.is_available() else "cpu"),
)

# ─── 변수 공간 (raw scale) ───────────────────────────────────
#   [standoff_distance, line_velocity, pressure]
bounds_raw = torch.tensor(
    [[0.15,   1.0,  30.0],      # lower
     [1.00,  50.0, 200.0]],     # upper
    **tkwargs
)

# ─── 실험 평가 함수 ──────────────────────────────────────────
def evaluate_X(x_raw: torch.Tensor, run_id: int) -> torch.Tensor:
    """x_raw: (3,) tensor in RAW scale  →  returns (2,) tensor(scores)."""
    # Tensor → Python float
    standoff_distance, line_velocity, pressure = x_raw.detach().cpu().tolist()

    # 장비 세팅 & 프린트
    inst.SetPressure(pressure)
    print_line_by_iter(run_id, ORIGIN_Z, standoff_distance, line_velocity)

    # 점수 계산 (score_1, score_2 반드시 2개!)
    score_1, score_2 = calculate_last_line_stddev(FILE_PATH)

    print(f"score 1 : {score_1}   score 2 : {score_2}")

    return torch.tensor([-score_1, score_2], **tkwargs)

# ─── 초기 설계 ───────────────────────────────────────────────
N_INIT = 8
train_X_raw = draw_sobol_samples(bounds=bounds_raw, n=1, q=N_INIT).squeeze(0)
train_Y     = torch.vstack([evaluate_X(x, i+1) for i, x in enumerate(train_X_raw)])

# ─── BO 루프 설정 ────────────────────────────────────────────
Q_BATCH        = 1
N_ITER         = 40
MC_SAMPLES     = 256
sampler        = SobolQMCNormalSampler(sample_shape=torch.Size([MC_SAMPLES]))
run_counter    = N_INIT + 1        # 실험 번호 이어서 사용

for step in range(1, N_ITER + 1):
    # 1. GP 모델 2개 → ModelListGP
    models = []
    for m in range(train_Y.shape[-1]):           # 2 objectives
        models.append(
            SingleTaskGP(
                train_X_raw,
                train_Y[..., m : m + 1],
                input_transform   = Normalize(d=3),
                outcome_transform = Standardize(m=1),
            )
        )
    model = ModelListGP(*models).to(**tkwargs)

    # 2. 모델 학습
    mll = SumMarginalLogLikelihood(model.likelihood, model)
    fit_gpytorch_mll(mll)        # BoTorch 0.14 : .fit() 지원

    # 3. 참조점 (Pareto보다 살짝 아래)
    ref_point = (train_Y.min(dim=0).values - 1e-3).tolist()

    # 4. qNEHVI 획득함수 (baseline은 raw X)
    acqf = qLogNoisyExpectedHypervolumeImprovement(
        model      = model,
        ref_point  = ref_point,
        X_baseline = train_X_raw,
        sampler    = sampler,
        prune_baseline = True,
    )

    # 5. 후보 탐색 (정규화 0-1 공간에서)
    bounds_unit = torch.stack(
        [torch.zeros(3, **tkwargs), torch.ones(3, **tkwargs)]
    )
    cand_unit, _ = optimize_acqf(
        acqf,
        bounds          = bounds_unit,
        q               = Q_BATCH,
        num_restarts    = 20,
        raw_samples     = 1024,
    )
    candidate_raw = unnormalize(cand_unit, bounds_raw).squeeze(0)

    # 6. 실험 수행 & 데이터 업데이트
    new_Y = evaluate_X(candidate_raw, run_counter)
    run_counter += 1

    train_X_raw = torch.cat([train_X_raw, candidate_raw.unsqueeze(0)])
    train_Y     = torch.cat([train_Y,     new_Y.unsqueeze(0)])

    # 7. 로그 출력
    print(f"[{step:02}]  ref={ref_point}  new Y={new_Y.tolist()}")

# ─── 결과 저장 ───────────────────────────────────────────────
ts = time.strftime("%Y%m%d_%H%M%S")
torch.save(
    {"X_raw": train_X_raw.cpu(), "Y": train_Y.cpu()},
    os.path.join(LOG_DIR, f"MOBO_qNEHVI_{ts}.pt"),
)
print(f"Saved data → {LOG_DIR}\\MOBO_qNEHVI_{ts}.pt")
