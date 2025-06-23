# mobo_qnehvi_5var.py  ────────────────────────────────────────────────────
"""
5 개의 설계변수
    0) inter_layer_standoff   [mm]   0.15 – 1.00
    1) n_ligaments            (int)  2    – 5
    2) line_velocity          [mm/s] 1.0  – 50.0
    3) num_layers             (int)  2    – 8
    4) pressure               [kPa]  30   – 200
first_layer_standoff 는 고정(코드 아래 ORIGIN-Z 및 FIRST_LAYER_STANDOFF 참고).
"""
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

# ─── 장비·평가 코드 ─────────────────────────────────────────────────────
from Lattice_printing import print_lattice_by_iter          # (run_id, …)
from Calculate_score  import calculate_lattice_scores       # → (score1, score2)
from NordsonEFD       import NordsonEFD

FILE_PATH = r"C:\FTP\Keyence\lj-s\result\SD2_001\250617_034122.txt"
LOG_DIR   = r"C:\Users\Administrator\Documents\JH\optimization_logs"
os.makedirs(LOG_DIR, exist_ok=True)

inst                     = NordsonEFD(port="COM5", baudrate=115200, timeout=1)
ORIGIN_Z                 = 15.0        # 베드 기준 원점 Z
FIRST_LAYER_STANDOFF     = 0.2        # 고정값

# ─── torch 기본 설정 ───────────────────────────────────────────────────
tkwargs = dict(
    dtype  = torch.double,
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu"),
)

# ─── 변수공간 (raw) ────────────────────────────────────────────────────
#   [inter_layer_standoff, n_ligaments, line_velocity, num_layers, pressure]
bounds_raw = torch.tensor(
    [
        [0.05, 1.0,  5.0, 1.0,  150.0],   # lower
        [0.3, 8.0, 30.0, 8.0, 300.0],   # upper
    ],
    **tkwargs,
)
D = bounds_raw.shape[-1]        # == 5

# ─── 평가 함수 ─────────────────────────────────────────────────────────
def evaluate_X(x_raw: torch.Tensor, run_id: int) -> torch.Tensor:
    """
    x_raw: (5,) RAW → returns (2,) tensor, 목적 2 개 (뒤집을 건 뒤집기).
    """
    (
        inter_layer_standoff,
        n_lig_raw,
        line_velocity,
        num_layers_raw,
        pressure,
    ) = x_raw.detach().cpu().tolist()

    # 정수 변수 변환/클램프
    n_ligaments = int(round(n_lig_raw))
    num_layers  = int(round(num_layers_raw))


    # 장비 세팅
    inst.SetPressure(pressure)

    # 프린트
    print_lattice_by_iter(
        run_id,
        ORIGIN_Z,
        FIRST_LAYER_STANDOFF,
        inter_layer_standoff,
        n_ligaments,
        line_velocity,
        num_layers
    )

    # 점수 계산 1: sav, 2: height avg
    score1, score2 = calculate_lattice_scores(FILE_PATH)
    print(f"[run {run_id}] volume score={score1:.4f}  surface area score={score2:.4f}")

    return torch.tensor([score1, score2], **tkwargs)  # score1 ↓ → 부호 반전

# ─── 초기 설계 ─────────────────────────────────────────────────────────
N_INIT = 10                                   # 초기 샘플
train_X_raw = draw_sobol_samples(bounds=bounds_raw, n=1, q=N_INIT).squeeze(0)
train_Y     = torch.vstack(
    [evaluate_X(x, i + 1) for i, x in enumerate(train_X_raw)]
)

# ─── BO 루프 ──────────────────────────────────────────────────────────
Q_BATCH     = 1
N_ITER      = 30
MC_SAMPLES  = 256
sampler     = SobolQMCNormalSampler(sample_shape=torch.Size([MC_SAMPLES]))
run_counter = N_INIT + 1

for step in range(1, N_ITER + 1):
    # 1. GP 모델 구축
    models = [
        SingleTaskGP(
            train_X_raw,
            train_Y[..., m : m + 1],
            input_transform   = Normalize(d=D),
            outcome_transform = Standardize(m=1),
        )
        for m in range(train_Y.shape[-1])
    ]
    model = ModelListGP(*models).to(**tkwargs)

    # 2. 학습
    mll = SumMarginalLogLikelihood(model.likelihood, model)
    fit_gpytorch_mll(mll)

    # 3. 참조점
    ref_point = (train_Y.min(dim=0).values - 1e-3).tolist()

    # 4. 획득함수
    acqf = qLogNoisyExpectedHypervolumeImprovement(
        model          = model,
        ref_point      = ref_point,
        X_baseline     = train_X_raw,
        sampler        = sampler,
        prune_baseline = True,
    )

    # 5. 최적화(단위공간)
    bounds_unit = torch.stack(
        [torch.zeros(D, **tkwargs), torch.ones(D, **tkwargs)]
    )
    cand_unit, _ = optimize_acqf(
        acqf,
        bounds       = bounds_unit,
        q            = Q_BATCH,
        num_restarts = 20,
        raw_samples  = 1024,
    )
    candidate_raw = unnormalize(cand_unit, bounds_raw).squeeze(0)

    # 6. 실험
    new_Y = evaluate_X(candidate_raw, run_counter)
    run_counter += 1

    # 7. 데이터 업데이트
    train_X_raw = torch.cat([train_X_raw, candidate_raw.unsqueeze(0)])
    train_Y     = torch.cat([train_Y,     new_Y.unsqueeze(0)])

    print(f"[{step:02}] ref={ref_point} newY={new_Y.tolist()}")

# ─── 결과 저장 ─────────────────────────────────────────────────────────
ts = time.strftime("%Y%m%d_%H%M%S")
torch.save(
    {"X_raw": train_X_raw.cpu(), "Y": train_Y.cpu()},
    os.path.join(LOG_DIR, f"MOBO_qNEHVI_{ts}.pt"),
)
print(f"Saved data → {LOG_DIR}\\MOBO_qNEHVI_{ts}.pt")
