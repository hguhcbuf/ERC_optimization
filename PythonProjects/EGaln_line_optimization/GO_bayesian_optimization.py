import numpy as np
import pandas as pd
import json
import time
from functools import lru_cache
from pathlib import Path
from datetime import datetime

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern
from scipy.stats import qmc
from scipy.special import expit
from scipy.optimize import minimize
from scipy.linalg import cho_factor, cho_solve
import warnings
from GO_make_pillar_array import (
    NOZZLE_DIAMETER, NOZZLE_RADIUS, ARRAY_SIZE, array_coordinates,
    REFERENCE_DIAMETER_MM,
    NOZZLE_OUTER_DIAMETER, DIE_SWELLING_RATIO, COLLISION_MARGIN_MM,
    collision_clearance_mm, disjoint_roi_surface_area, pillar_radius_mm,
)


# ============================================================
# RESUME SETTINGS
# ============================================================

# 새 실험 시작
# RESUME_FROM_CSV = None

# 예전 실험 이어하기
RESUME_FROM_CSV = None  # New ROI/score: do not resume old 8 mm measurements.

# ============================================================
# 0. USER SETTINGS
# ============================================================

# ------------------------------------------------------------
# Set BO_MODE and VANILLA_NOZZLE_CLEARANCE; start a NEW run for comparisons.
# Shared initial LHS: bounds only in BOTH modes (including G-code).
# physics: geometry/buckling prior + nozzle clearance filter after LHS.
# vanilla: zero-mean GP + optional nozzle clearance filter after LHS.
# Neither mode adds a pillar-to-pillar overlap rejection rule.
# Same dimensionless variables, bounds, measurements and UCB in both modes.
# ------------------------------------------------------------
BO_MODE = "vanilla"  # "physics" or "vanilla"
VANILLA_NOZZLE_CLEARANCE = True  # True: nozzle constraint; False: bounds only
if BO_MODE not in ("physics", "vanilla"):
    raise ValueError("BO_MODE must be 'physics' or 'vanilla'.")
PRIOR_MODE = "geometry_buckling" if BO_MODE == "physics" else "zero"
USE_NOZZLE_CLEARANCE = BO_MODE == "physics" or (
    BO_MODE == "vanilla" and VANILLA_NOZZLE_CLEARANCE
)
COLLISION_POLICY = "nozzle_only" if USE_NOZZLE_CLEARANCE else "bounds_only"


# ------------------------------------------------------------
# BO settings
# ------------------------------------------------------------

N_INITIAL = 8
N_BO = 64

BETA = 6.636

# Observation variance in mm^4 (standard deviation = 2 mm^2).
# Shared by joint marginal-likelihood optimization and final GP fitting.
GP_NOISE_VARIANCE = 4.0
# Bounds in normalized (0-1) input coordinates.
GP_LENGTH_SCALE_BOUNDS = (0.03, 1e3)

N_CANDIDATES = 30000

RANDOM_SEED = 0


# ------------------------------------------------------------
# Save settings
# ------------------------------------------------------------

SAVE_ITERATION_SNAPSHOTS = True

BASE_SAVE_DIR = Path("bo_logs")


# ------------------------------------------------------------
# Automatic printing / measurement settings (machine coordinates: mm)
# Check these against the loaded substrate and the PLC G-code directory.
# Slot pitch is independent of the 5 mm profiler ROI.
# Output retains the first base-grid point beyond the ROI for edge coverage.
# ------------------------------------------------------------
file_path = r"C:\FTP\Keyence\lj-s\result\SD1_002\260919_135021.txt"
PRINT_START_X = 30.0
PRINT_START_Y = 320.0
PRINT_INITIAL_HEIGHT = 10.045
ARRAYS_PER_ROW = 9
ARRAY_PITCH_X = 16.0
ARRAY_PITCH_Y = 16.0
GCODE_TIMEOUT = 7200.0
POST_GCODE_DELAY_SECONDS = 2.0
MEASUREMENT_STABLE_SECONDS = 0.2
CAPTURE_SERVER_IP = "192.168.0.3"
CAPTURE_PORT = 5000
CAPTURE_TIMEOUT = 30.0
PROFILE_SPACING_UM = 5.0
PROFILE_LENGTH_UNIT = "mm"  # confirmed profiler output unit
EXPECTED_PROFILE_COUNT = round(ARRAY_SIZE * 1000 / PROFILE_SPACING_UM)  # 1000
MIN_PROFILE_LENGTH_MM = ARRAY_SIZE
MEASUREMENT_SCHEMA = "roi5_clamped_profiles_inverseV_shared_lhs_v7"
MEASUREMENT_TIMEOUT = 30.0

# Objective and all measured/predicted areas are in mm^2.
OBJECTIVE_NAME = "profiler_surface_area_mm2"
INPUT_SCHEMA = "H_star=h/(D*B),V_star=v_lift/v_extrudate,d_star=d/(D*B);v4"


# ============================================================
# 1. Experimental variable bounds
#
# x = [H*, V*, d*]; H*=height/(D*B), d*=grid pitch/(D*B).
# Divide old H*, d* bounds by B to preserve the existing physical search range.
# ============================================================

bounds = {
    "H_star": (2.0, 10),
    "V_star": (0.01, 1.0),
    "d_star": (2.0, 10.0),
}

names = list(bounds.keys())

lower = np.array([
    bounds[name][0]
    for name in names
])

upper = np.array([
    bounds[name][1]
    for name in names
])


# Buckling is a soft mean-function assumption, NOT a feasibility constraint.
# q = H* V*. These initial guesses are numerical defaults, not measured limits.
# None chooses a broad transition from the CURRENT variable bounds.
BUCKLING_C_INITIAL = None  # If old C=1.6, use 1.6 / DIE_SWELLING_RATIO here.
BUCKLING_TAU_INITIAL = None
BUCKLING_RHO_INITIAL = 0.30
BUCKLING_MIN_SAMPLES = 8
BUCKLING_RESTARTS = 16
BUCKLING_MAXITER = 300
# Weak quadratic penalty in [log(C), log(tau), rho]; makes this regularized
# marginal-likelihood fitting (MAP-style), not pure maximum likelihood.
BUCKLING_REGULARIZATION = 1.0
BUCKLING_PRIOR_SCALES = np.array([2.0, 1.5, 0.4])


# ============================================================
# 2. Fixed geometry
# ============================================================

DEVICE_SIZE = ARRAY_SIZE  # profiler ROI side length, mm

# Nozzle diameter/radius are imported from GO_make_pillar_array (single source).


# ============================================================
# 3. Geometry-informed prior
# ============================================================

def collision_free(X):
    X = np.atleast_2d(np.asarray(X, dtype=float))
    valid = np.isfinite(X).all(axis=1) & (X > 0).all(axis=1)
    allowed = np.zeros(len(X), dtype=bool)
    allowed[valid] = collision_clearance_mm(X[valid, 1], X[valid, 2]) >= 0
    return allowed


def candidates_allowed(X):
    """BO box bounds and optional nozzle constraint in either mode."""
    X = np.atleast_2d(np.asarray(X, dtype=float))
    allowed = (np.isfinite(X).all(axis=1) & (X > 0).all(axis=1)
               & (X >= lower).all(axis=1) & (X <= upper).all(axis=1))
    if USE_NOZZLE_CLEARANCE:
        allowed &= collision_free(X)
    return allowed


def geometry_mean(X):
    """Total exposed surface in profiler ROI, including uncovered substrate."""
    from GO_make_pillar_array import estimate_array_surface_area
    X = np.atleast_2d(np.asarray(X, dtype=float))
    if X.shape[1] != 3 or not np.isfinite(X).all() or np.any(X <= 0):
        raise ValueError("Expected positive finite [H_star, V_star, d_star].")
    radius = pillar_radius_mm(X[:, 1])
    disjoint = X[:, 2]*REFERENCE_DIAMETER_MM/np.sqrt(2) >= 2*radius
    area = np.empty(len(X))
    if disjoint.any():
        area[disjoint] = disjoint_roi_surface_area(X[disjoint])
    for i in np.flatnonzero(~disjoint):
        area[i] = estimate_array_surface_area(X[i,0], X[i,1],
                    array_coordinates(X[i,2]))["surface_area_mm2"]
    return area


def buckling_defaults():
    q_min = lower[0] * lower[1]
    q_max = upper[0] * upper[1]
    span = max(q_max - q_min, 1e-3)
    return {
        "C": float(BUCKLING_C_INITIAL if BUCKLING_C_INITIAL is not None
                   else (q_min + q_max) / 2),
        "tau": float(BUCKLING_TAU_INITIAL if BUCKLING_TAU_INITIAL is not None
                     else span / 2),
        "rho": float(BUCKLING_RHO_INITIAL),
    }


def buckling_factor(X, params):
    X = np.atleast_2d(np.asarray(X, dtype=float))
    q = X[:, 0] * X[:, 1]
    return params["rho"] + (1 - params["rho"]) * expit(
        (params["C"] - q) / params["tau"]
    )


def get_prior_mean(X, gp=None):
    """m(x) = ROI_area + (S_geom(x)-ROI_area) * buckling_factor(x).

    C is a soft transition location, tau its width, rho retained area fraction.
    Use parameters attached to THIS fitted GP, never global fitted state.
    These fitted parameters describe objective trends, not a validated boundary.
    """
    X = np.atleast_2d(X)
    mode = getattr(gp, "prior_mode_", PRIOR_MODE)
    if mode == "zero":
        return np.zeros(X.shape[0])
    if mode == "geometry":
        return geometry_mean(X)
    if mode == "geometry_buckling":
        params = getattr(gp, "buckling_params_", None) or buckling_defaults()
        return ARRAY_SIZE**2 + (geometry_mean(X) - ARRAY_SIZE**2) * buckling_factor(X, params)
    raise ValueError("PRIOR_MODE must be 'geometry_buckling', 'geometry' or 'zero'.")


def get_prior_for_log(X, gp=None):
    if getattr(gp, "prior_mode_", PRIOR_MODE) == "zero":
        return np.full(np.atleast_2d(X).shape[0], np.nan)
    return get_prior_mean(X, gp=gp)


# ============================================================
# 6. Input normalization
# ============================================================

def normalize_X(X):

    X = np.atleast_2d(X)

    return (
        (X - lower)
        /
        (upper - lower)
    )


# ============================================================
# 7. GP fitting
# ============================================================

def fit_gp(X_obs, y_obs):
    X_obs = np.asarray(X_obs, dtype=float)
    y_obs = np.asarray(y_obs, dtype=float)
    if not np.all(np.isfinite(y_obs)):
        raise ValueError("Observations must be finite.")
    X_norm = normalize_X(X_obs)
    kernel = ConstantKernel(1.0, (1e-6, 1e6)) * Matern(
        length_scale=np.ones(3), length_scale_bounds=GP_LENGTH_SCALE_BOUNDS, nu=2.5
    )
    params = None
    fit_info = {"learned": False, "success": False, "penalty": np.nan,
                "message": "not applicable"}

    if PRIOR_MODE == "geometry_buckling":
        params = buckling_defaults()
        if params["C"] <= 0 or params["tau"] <= 0 or not 0 <= params["rho"] <= 1:
            raise ValueError("Require C > 0, tau > 0 and 0 <= rho <= 1.")
        if len(y_obs) >= BUCKLING_MIN_SAMPLES:
            area = geometry_mean(X_obs) - ARRAY_SIZE**2
            q = X_obs[:, 0] * X_obs[:, 1]
            center = np.array([np.log(params["C"]), np.log(params["tau"]), params["rho"]])
            qmax = upper[0] * upper[1]
            span = max(qmax - lower[0] * lower[1], 1e-3)
            mean_bounds = np.array([
                [np.log(min(1e-4, params["C"] / 10)), np.log(max(10*qmax, params["C"]*10))],
                [np.log(min(0.02*span, params["tau"]/10)), np.log(max(10*span, params["tau"]*10))],
                [0.0, 1.0],
            ])
            all_bounds = np.vstack([kernel.bounds, mean_bounds])
            nk = len(kernel.theta)

            def objective(theta):
                C, tau = np.exp(theta[nk:nk+2])
                rho = theta[nk+2]
                prob = expit((C - q) / tau)
                mean = ARRAY_SIZE**2 + area * (rho + (1-rho)*prob)
                residual = y_obs - mean
                K, K_grad = kernel.clone_with_theta(theta[:nk])(X_norm, eval_gradient=True)
                K[np.diag_indices_from(K)] += GP_NOISE_VARIANCE
                try:
                    factor = cho_factor(K, lower=True, check_finite=False)
                    alpha = cho_solve(factor, residual, check_finite=False)
                    inverse = cho_solve(factor, np.eye(len(y_obs)), check_finite=False)
                except np.linalg.LinAlgError:
                    return 1e100, np.zeros_like(theta)
                nll = (0.5 * residual @ alpha
                       + np.log(np.diag(factor[0])).sum()
                       + 0.5 * len(y_obs) * np.log(2*np.pi))
                grad_kernel = 0.5*np.einsum(
                    "ij,ijk->k", inverse - np.outer(alpha, alpha), K_grad
                )
                common = area*(1-rho)*prob*(1-prob)
                dmean = np.column_stack([
                    common*C/tau, common*(q-C)/tau, area*(1-prob)
                ])
                delta = (theta[nk:] - center) / BUCKLING_PRIOR_SCALES
                penalty = 0.5*BUCKLING_REGULARIZATION*(delta @ delta)
                grad_mean = (-dmean.T @ alpha + BUCKLING_REGULARIZATION
                             * delta / BUCKLING_PRIOR_SCALES)
                return nll + penalty, np.r_[grad_kernel, grad_mean]

            rng = np.random.default_rng(RANDOM_SEED)
            start = np.r_[kernel.theta, center]
            best_theta = start.copy()
            best_value = objective(start)[0]
            best_result = None
            for restart in range(BUCKLING_RESTARTS + 1):
                trial = start.copy()
                if restart:
                    trial += rng.normal(0, 1, len(trial))
                    trial = np.clip(trial, all_bounds[:, 0], all_bounds[:, 1])
                result = minimize(objective, trial, jac=True, method="L-BFGS-B",
                                  bounds=all_bounds, options={"maxiter": BUCKLING_MAXITER})
                if np.isfinite(result.fun) and result.fun < best_value:
                    best_theta, best_value, best_result = result.x, result.fun, result
            kernel = kernel.clone_with_theta(best_theta[:nk])
            params = {"C": float(np.exp(best_theta[nk])),
                      "tau": float(np.exp(best_theta[nk+1])),
                      "rho": float(best_theta[nk+2])}
            penalty = 0.5*BUCKLING_REGULARIZATION*np.sum(
                ((best_theta[nk:]-center)/BUCKLING_PRIOR_SCALES)**2
            )
            fit_info = {"learned": best_result is not None,
                        "success": bool(best_result is not None and best_result.success),
                        "penalty": float(penalty),
                        "message": str(best_result.message) if best_result is not None
                                   else "No improvement; retained initial parameters"}
            if not fit_info["success"]:
                warnings.warn("Buckling fit: " + fit_info["message"])
        else:
            fit_info["message"] = "Too few observations; using broad initial mean"

    if params is None:
        mean = get_prior_mean(X_obs)
    else:
        mean = ARRAY_SIZE**2 + (geometry_mean(X_obs) - ARRAY_SIZE**2) * buckling_factor(X_obs, params)
    joint_fit = PRIOR_MODE == "geometry_buckling" and len(y_obs) >= BUCKLING_MIN_SAMPLES
    gp = GaussianProcessRegressor(
        kernel=kernel, alpha=GP_NOISE_VARIANCE, normalize_y=False,
        optimizer=None if joint_fit else "fmin_l_bfgs_b",
        n_restarts_optimizer=0 if joint_fit else 10, random_state=RANDOM_SEED,
    )
    gp.fit(X_norm, y_obs - mean)
    gp.prior_mode_ = PRIOR_MODE
    gp.buckling_params_ = params
    gp.buckling_fit_info_ = fit_info
    # Predictive std is conditional on the fitted mean parameters; it does not
    # include uncertainty in C/tau/rho. No feasibility mask or boundary search.
    return gp


# ============================================================
# 8. Prediction
# ============================================================

def predict_surface(gp, X):

    X = np.atleast_2d(X)

    X_norm = normalize_X(X)


    # --------------------------------------------------------
    # GP predicts residual / correction
    # --------------------------------------------------------

    mu_gp, std = gp.predict(
        X_norm,
        return_std=True
    )


    # --------------------------------------------------------
    # Prior mean
    # --------------------------------------------------------

    m = get_prior_mean(X, gp=gp)


    # --------------------------------------------------------
    # Final predicted surface area
    # --------------------------------------------------------

    mu_total = (
        m
        +
        mu_gp
    )


    return (
        mu_total,
        std,
        mu_gp
    )


# ============================================================
# 9. UCB
# ============================================================

def ucb(
    gp,
    X,
    beta=BETA
):

    mu, std, _ = predict_surface(
        gp,
        X
    )

    acquisition = (
        mu
        +
        np.sqrt(beta)
        * std
    )

    return acquisition


# ============================================================
# 10. Suggest next point
# ============================================================

def suggest_next(
    gp,
    n_candidates=N_CANDIDATES,
    beta=BETA
):

    candidates = np.random.uniform(
        lower,
        upper,
        size=(
            n_candidates,
            3
        )
    )


    candidates = candidates[candidates_allowed(candidates)]
    if not len(candidates):
        raise ValueError("No collision-free BO candidates; widen spacing bounds.")

    acquisition = ucb(
        gp,
        candidates,
        beta=beta
    )


    best_idx = np.argmax(
        acquisition
    )


    x_next = candidates[
        best_idx
    ]


    (
        mu,
        std,
        mu_gp
    ) = predict_surface(
        gp,
        x_next.reshape(1, -1)
    )


    return {
        "x": x_next,

        "predicted_total": mu[0],

        "predicted_std": std[0],

        "predicted_gp_component": mu_gp[0],

        "acquisition": acquisition[
            best_idx
        ]
    }


# ============================================================
# 11. Initial Latin Hypercube sampling
# ============================================================

def generate_initial_points(
    n=N_INITIAL,
    seed=RANDOM_SEED
):

    # Identical, unfiltered LHS in both modes for equal n, seed and bounds.
    sampler = qmc.LatinHypercube(d=3, seed=seed)
    return qmc.scale(sampler.random(n=n), lower, upper)


# ============================================================
# 12. Extract GP information safely
#
# If something does not exist,
# automatically return NaN
# ============================================================

def safe_value(func):

    try:

        value = func()

        return value

    except Exception:

        return np.nan


def extract_gp_state(gp):

    if gp is None:

        return {
            "kernel_constant": np.nan,
            "signal_std": np.nan,

            "length_scale_H_star": np.nan,
            "length_scale_V_star": np.nan,
            "length_scale_d_star": np.nan,

            "log_marginal_likelihood": np.nan,

            "kernel_theta": np.nan,
            "kernel_hyperparameter_names": np.nan,

            "kernel_repr": np.nan,

            "noise_alpha": np.nan,
        }


    # --------------------------------------------------------
    # Constant kernel
    # --------------------------------------------------------

    constant_value = safe_value(
        lambda:
        gp.kernel_.k1.constant_value
    )


    # Kernel constant is variance-like.
    # sqrt is useful as signal amplitude.
    if np.isfinite(
        constant_value
    ):

        signal_std = np.sqrt(
            constant_value
        )

    else:

        signal_std = np.nan


    # --------------------------------------------------------
    # Length scales
    # --------------------------------------------------------

    length_scales = safe_value(
        lambda:
        np.asarray(
            gp.kernel_.k2.length_scale
        )
    )


    try:

        ls_H = float(
            length_scales[0]
        )

        ls_V = float(
            length_scales[1]
        )

        ls_d = float(
            length_scales[2]
        )

    except Exception:

        ls_H = np.nan
        ls_V = np.nan
        ls_d = np.nan


    # --------------------------------------------------------
    # Raw theta
    #
    # sklearn stores kernel theta in log-space.
    # Save it too.
    # --------------------------------------------------------

    theta = safe_value(
        lambda:
        json.dumps(
            gp.kernel_.theta.tolist()
        )
    )


    hp_names = safe_value(
        lambda:
        json.dumps([
            hp.name
            for hp
            in gp.kernel_.hyperparameters
        ])
    )


    # --------------------------------------------------------
    # Noise alpha
    # --------------------------------------------------------

    noise_alpha = safe_value(
        lambda:
        float(gp.alpha)
    )


    return {

        "kernel_constant":
            constant_value,

        "signal_std":
            signal_std,

        "length_scale_H_star":
            ls_H,

        "length_scale_V_star":
            ls_V,

        "length_scale_d_star":
            ls_d,

        "log_marginal_likelihood":
            safe_value(
                lambda:
                float(
                    gp.log_marginal_likelihood_value_
                )
            ),

        "kernel_theta":
            theta,

        "kernel_hyperparameter_names":
            hp_names,

        "kernel_repr":
            safe_value(
                lambda:
                str(gp.kernel_)
            ),

        "noise_alpha":
            noise_alpha,
    }


# ============================================================
# 13. GP target statistics
# ============================================================

def get_gp_target_stats(
    X_obs,
    y_obs,
    gp=None
):

    try:

        X_obs = np.asarray(
            X_obs
        )

        y_obs = np.asarray(
            y_obs
        )


        m = get_prior_mean(
            X_obs, gp=gp
        )


        target = (
            y_obs - m
        )


        return {
            "gp_target_mean":
                float(
                    np.mean(target)
                ),

            "gp_target_std":
                float(
                    np.std(target)
                ),

            "gp_target_min":
                float(
                    np.min(target)
                ),

            "gp_target_max":
                float(
                    np.max(target)
                ),
        }

    except Exception:

        return {
            "gp_target_mean": np.nan,
            "gp_target_std": np.nan,
            "gp_target_min": np.nan,
            "gp_target_max": np.nan,
        }


# ============================================================
# 14. Save history
# ============================================================

def save_history(
    history,
    session_dir,
    iteration_number=None
):

    df = pd.DataFrame(
        history
    )


    # --------------------------------------------------------
    # Main cumulative CSV
    #
    # Updated after every experiment
    # --------------------------------------------------------

    main_path = (
        session_dir
        /
        "bo_full_history.csv"
    )

    df.to_csv(
        main_path,
        index=False
    )


    # --------------------------------------------------------
    # Optional iteration-by-iteration snapshot
    # --------------------------------------------------------

    if (
        SAVE_ITERATION_SNAPSHOTS
        and
        iteration_number is not None
    ):

        snapshot_path = (
            session_dir
            /
            (
                f"snapshot_"
                f"{iteration_number:03d}.csv"
            )
        )

        df.to_csv(
            snapshot_path,
            index=False
        )


    return main_path


# ============================================================
# 15. Create one complete history row
# ============================================================

def make_history_row(

    experiment_number,

    phase,

    x,

    measured_surface_area,

    best_so_far,

    pre_gp=None,

    post_gp=None,

    recommendation_info=None,

    X_after=None,

    y_after=None,
    measurement_info=None
):

    H_star = x[0]
    V_star = x[1]
    d_star = x[2]
    d = d_star * REFERENCE_DIAMETER_MM


    # --------------------------------------------------------
    # Prior information
    # --------------------------------------------------------

    prior_log = get_prior_for_log(
        x.reshape(1, -1), gp=post_gp
    )[0]


    if PRIOR_MODE in ("geometry", "geometry_buckling"):

        residual = (
            measured_surface_area
            -
            prior_log
        )

    else:

        # User requested:
        # unavailable / irrelevant values -> NaN
        residual = np.nan


    # --------------------------------------------------------
    # What GP actually learns
    # --------------------------------------------------------

    if PRIOR_MODE in ("geometry", "geometry_buckling"):

        gp_target_value = residual

    else:

        gp_target_value = (
            measured_surface_area
        )


    # --------------------------------------------------------
    # PRE model
    #
    # Model used to choose this BO point
    # --------------------------------------------------------

    pre = extract_gp_state(
        pre_gp
    )


    # --------------------------------------------------------
    # POST model
    #
    # Model after adding measured result
    # --------------------------------------------------------

    post = extract_gp_state(
        post_gp
    )


    # --------------------------------------------------------
    # Recommendation info
    # --------------------------------------------------------

    if recommendation_info is None:

        recommended_H = np.nan
        recommended_V = np.nan
        recommended_d = np.nan

        predicted_total = np.nan
        predicted_std = np.nan
        predicted_gp_component = np.nan
        acquisition_value = np.nan

        prediction_error = np.nan

    else:

        recommended_H = (
            recommendation_info["x"][0]
        )

        recommended_V = (
            recommendation_info["x"][1]
        )

        recommended_d = (
            recommendation_info["x"][2]
        )

        predicted_total = (
            recommendation_info[
                "predicted_total"
            ]
        )

        predicted_std = (
            recommendation_info[
                "predicted_std"
            ]
        )

        predicted_gp_component = (
            recommendation_info[
                "predicted_gp_component"
            ]
        )

        acquisition_value = (
            recommendation_info[
                "acquisition"
            ]
        )

        prediction_error = (
            measured_surface_area
            -
            predicted_total
        )


    # --------------------------------------------------------
    # Post-update GP target statistics
    # --------------------------------------------------------

    if (
        X_after is not None
        and
        y_after is not None
    ):

        target_stats = (
            get_gp_target_stats(
                X_after,
                y_after, gp=post_gp
            )
        )

    else:

        target_stats = {
            "gp_target_mean": np.nan,
            "gp_target_std": np.nan,
            "gp_target_min": np.nan,
            "gp_target_max": np.nan,
        }


    # --------------------------------------------------------
    # Row
    # --------------------------------------------------------

    row = {

        # ====================================================
        # Experiment identification
        # ====================================================

        "timestamp":
            datetime.now().isoformat(
                timespec="seconds"
            ),

        "experiment_number":
            experiment_number,

        "phase":
            phase,

        "prior_mode":
            PRIOR_MODE,


        # ====================================================
        # Actual experiment
        # ====================================================

        "H_star":
            H_star,

        "V_star":
            V_star,

        "d_star":
            d_star,

        "d_mm":
            d,

        "measured_surface_area_mm2":
            measured_surface_area,

        "best_surface_area_so_far_mm2":
            best_so_far,


        # ====================================================
        # Prior / residual
        # ====================================================

        "prior_mean_mm2":
            prior_log,

        "residual_mm2":
            residual,

        "gp_training_target":
            gp_target_value,


        # ====================================================
        # Recommendation
        # ====================================================

        "recommended_H_star":
            recommended_H,

        "recommended_V_star":
            recommended_V,

        "recommended_d_star":
            recommended_d,

        "recommended_d_mm":
            recommended_d * REFERENCE_DIAMETER_MM,

        "predicted_surface_area_mm2":
            predicted_total,

        "predicted_std_mm2":
            predicted_std,

        "predicted_gp_component_mm2":
            predicted_gp_component,

        "acquisition_UCB":
            acquisition_value,

        "prediction_error_mm2":
            prediction_error,


        # ====================================================
        # PRE-update GP hyperparameters
        #
        # These generated the recommendation
        # ====================================================

        "pre_kernel_constant":
            pre[
                "kernel_constant"
            ],

        "pre_signal_std":
            pre[
                "signal_std"
            ],

        "pre_length_scale_H_star":
            pre[
                "length_scale_H_star"
            ],

        "pre_length_scale_V_star":
            pre[
                "length_scale_V_star"
            ],

        "pre_length_scale_d_star":
            pre[
                "length_scale_d_star"
            ],

        "pre_log_marginal_likelihood":
            pre[
                "log_marginal_likelihood"
            ],

        "pre_noise_alpha":
            pre[
                "noise_alpha"
            ],

        "pre_kernel_theta":
            pre[
                "kernel_theta"
            ],

        "pre_kernel_hyperparameter_names":
            pre[
                "kernel_hyperparameter_names"
            ],

        "pre_kernel_repr":
            pre[
                "kernel_repr"
            ],


        # ====================================================
        # POST-update GP hyperparameters
        #
        # Model after new measurement is added
        # ====================================================

        "post_kernel_constant":
            post[
                "kernel_constant"
            ],

        "post_signal_std":
            post[
                "signal_std"
            ],

        "post_length_scale_H_star":
            post[
                "length_scale_H_star"
            ],

        "post_length_scale_V_star":
            post[
                "length_scale_V_star"
            ],

        "post_length_scale_d_star":
            post[
                "length_scale_d_star"
            ],

        "post_log_marginal_likelihood":
            post[
                "log_marginal_likelihood"
            ],

        "post_noise_alpha":
            post[
                "noise_alpha"
            ],

        "post_kernel_theta":
            post[
                "kernel_theta"
            ],

        "post_kernel_hyperparameter_names":
            post[
                "kernel_hyperparameter_names"
            ],

        "post_kernel_repr":
            post[
                "kernel_repr"
            ],


        # ====================================================
        # GP training-target statistics
        # ====================================================

        "gp_target_mean":
            target_stats[
                "gp_target_mean"
            ],

        "gp_target_std":
            target_stats[
                "gp_target_std"
            ],

        "gp_target_min":
            target_stats[
                "gp_target_min"
            ],

        "gp_target_max":
            target_stats[
                "gp_target_max"
            ],


        # ====================================================
        # BO settings
        # ====================================================

        "beta":
            BETA,

        "n_candidates":
            N_CANDIDATES,

        "random_seed":
            RANDOM_SEED,


        # ====================================================
        # Geometry settings
        # ====================================================

        "device_size_mm":
            DEVICE_SIZE,

        "nozzle_diameter_mm":
            NOZZLE_DIAMETER,


        # ====================================================
        # Search bounds
        # ====================================================

        "H_star_lower":
            bounds["H_star"][0],

        "H_star_upper":
            bounds["H_star"][1],

        "V_star_lower":
            bounds["V_star"][0],

        "V_star_upper":
            bounds["V_star"][1],

        "d_star_lower":
            bounds["d_star"][0],

        "d_lower_mm":
            bounds["d_star"][0] * REFERENCE_DIAMETER_MM,

        "d_star_upper":
            bounds["d_star"][1],

        "d_upper_mm":
            bounds["d_star"][1] * REFERENCE_DIAMETER_MM,
    }


    start_x, start_y = experiment_position(experiment_number)
    row.update({
        "reference_diameter_mm": REFERENCE_DIAMETER_MM,
        "measurement_schema": MEASUREMENT_SCHEMA,
        "roi_side_mm": ARRAY_SIZE,
        "min_profile_length_mm": MIN_PROFILE_LENGTH_MM,
        "nozzle_outer_diameter_mm": NOZZLE_OUTER_DIAMETER,
        "die_swelling_ratio": DIE_SWELLING_RATIO,
        "bo_mode": BO_MODE,
        "nozzle_clearance_enabled": USE_NOZZLE_CLEARANCE and phase == "BO",
        "initial_sampling_policy": "shared_unfiltered_lhs",
        "collision_policy": COLLISION_POLICY,
        "collision_margin_mm": COLLISION_MARGIN_MM,
        "predicted_pillar_diameter_mm": float(2 * pillar_radius_mm(x[1])) if USE_NOZZLE_CLEARANCE else np.nan,
        "required_neighbor_distance_mm": float(pillar_radius_mm(x[1]) + NOZZLE_OUTER_DIAMETER/2 + COLLISION_MARGIN_MM) if USE_NOZZLE_CLEARANCE else np.nan,
        "collision_clearance_mm": float(collision_clearance_mm(x[1], x[2])) if USE_NOZZLE_CLEARANCE else np.nan,
        "objective_name": OBJECTIVE_NAME,
        "input_schema": INPUT_SCHEMA,
        "profiler_surface_area_mm2": measured_surface_area,
        "pillar_height_mm": H_star * REFERENCE_DIAMETER_MM,
        "profile_spacing_um": PROFILE_SPACING_UM,
        "profile_length_unit": PROFILE_LENGTH_UNIT,
        "expected_profile_count": EXPECTED_PROFILE_COUNT,
        "objective_score": measured_surface_area,
        "array_start_x_mm": start_x,
        "array_start_y_mm": start_y,
        "print_initial_height_mm": PRINT_INITIAL_HEIGHT,
        "measurement_file": file_path,
        "prior_model": "roi_baseline_soft_buckling_inverseV_v4" if PRIOR_MODE == "geometry_buckling" else ("zero_mean" if PRIOR_MODE == "zero" else "roi_clipped_union_inverseV_v4"),
    })
    row["H_star_times_V_star"] = float(H_star * V_star)
    row["geometry_unattenuated_mm2"] = (float(geometry_mean(x)[0])
                                        if PRIOR_MODE != "zero" else np.nan)
    row["initial_buckling_C"] = buckling_defaults()["C"] if PRIOR_MODE == "geometry_buckling" else np.nan
    for name in ("tau", "rho"):
        row[f"initial_buckling_{name}"] = buckling_defaults()[name] if PRIOR_MODE == "geometry_buckling" else np.nan
    row["buckling_regularization"] = BUCKLING_REGULARIZATION if PRIOR_MODE == "geometry_buckling" else np.nan
    for prefix, model in (("pre", pre_gp), ("post", post_gp)):
        params = getattr(model, "buckling_params_", None)
        info = getattr(model, "buckling_fit_info_", {})
        for name in ("C", "tau", "rho"):
            row[f"{prefix}_buckling_{name}"] = params[name] if params else np.nan
        row[f"{prefix}_buckling_factor"] = float(buckling_factor(x, params)[0]) if params else np.nan
        row[f"{prefix}_prior_mean_mm2"] = float(get_prior_for_log(x, gp=model)[0]) if model is not None else np.nan
        row[f"{prefix}_buckling_parameters_learned"] = info.get("learned", np.nan) if params else np.nan
        row[f"{prefix}_buckling_fit_success"] = info.get("success", np.nan) if params else np.nan
        row[f"{prefix}_buckling_fit_message"] = info.get("message", "") if params else np.nan
        row[f"{prefix}_buckling_penalty"] = info.get("penalty", np.nan) if params else np.nan
        row[f"{prefix}_regularized_log_marginal_likelihood"] = (
            float(model.log_marginal_likelihood_value_ - info.get("penalty", np.nan))
            if params else np.nan
        )
    for key in ("capture_filename", "capture_response", "capture_requested_at",
                "capture_acknowledged_at", "measurement_completed_at"):
        row[key] = (measurement_info or {}).get(key, np.nan)
    return row


# ============================================================
# 16. Automatic experiment and Bayesian Optimization loop
# ============================================================

def experiment_position(experiment_number):
    """One-based experiment number maps to an unused substrate slot."""
    if experiment_number < 1 or ARRAYS_PER_ROW < 1:
        raise ValueError("Experiment number and ARRAYS_PER_ROW must be positive.")
    row, col = divmod(experiment_number - 1, ARRAYS_PER_ROW)
    return (PRINT_START_X + col * ARRAY_PITCH_X,
            PRINT_START_Y + row * ARRAY_PITCH_Y)


def measurement_signature():
    path = Path(file_path)
    if not path.exists():
        return None
    stat = path.stat()
    return stat.st_mtime_ns, stat.st_size


def run_automatic_experiment(x, experiment_number, phase="BO"):
    from GO_make_pillar_array import write_light_harvesting_gcode
    from PLC_motion_controller_mod import run_gcode_file, wait_ready
    from GO_functions import calculate_surface_area, trigger_capture

    x = np.asarray(x, dtype=float)
    if x.shape != (3,) or not np.all(np.isfinite(x)) or np.any(x <= 0):
        raise ValueError("Expected positive finite [H_star, V_star, d_star].")
    if phase not in ("initial", "BO"):
        raise ValueError("phase must be initial or BO.")
    enforce_clearance = USE_NOZZLE_CLEARANCE and phase == "BO"
    if np.any(x < lower) or np.any(x > upper):
        raise ValueError("Candidate outside configured bounds.")
    if enforce_clearance and not collision_free(x)[0]:
        raise ValueError("BO candidate rejected by nozzle-clearance policy.")
    start_x, start_y = experiment_position(experiment_number)
    print(f"Array origin: X={start_x:.3f}, Y={start_y:.3f}")
    generated = write_light_harvesting_gcode(
        v_star=float(x[1]), h=float(x[0]), d_star=float(x[2]),
        start_x=start_x, start_y=start_y, initial_height=PRINT_INITIAL_HEIGHT,
        enforce_nozzle_clearance=enforce_clearance,
    )
    previous_signature = measurement_signature()
    if not run_gcode_file(Path(generated["path"]).name):
        raise RuntimeError("G-code launch failed; experiment was not recorded.")
    # Existing PLC handshake: run_gcode_file observes busy; wait_ready waits
    # for the ready state after program completion (M30).
    wait_ready(timeout=GCODE_TIMEOUT)
    time.sleep(POST_GCODE_DELAY_SECONDS)

    filename = (f"GO_{datetime.now():%Y%m%d_%H%M%S_%f}_exp{experiment_number:04d}"
                f"_H{x[0]:.5f}_V{x[1]:.5f}_dstar{x[2]:.5f}.png")
    measurement = {"capture_filename": filename,
                   "capture_requested_at": datetime.now().isoformat(timespec="milliseconds")}
    # Synchronous request: no background thread can race the area calculation.
    measurement["capture_response"] = trigger_capture(
        filename, server_ip=CAPTURE_SERVER_IP, port=CAPTURE_PORT, timeout=CAPTURE_TIMEOUT
    )
    measurement["capture_acknowledged_at"] = datetime.now().isoformat(timespec="milliseconds")

    # M50 may update the profiler file BEFORE M30/camera capture. Compare
    # against the signature saved BEFORE G-code launch, not after capture.
    deadline = time.monotonic() + MEASUREMENT_TIMEOUT
    while True:
        try:
            signature = measurement_signature()
            if signature is not None and signature != previous_signature:
                time.sleep(MEASUREMENT_STABLE_SECONDS)
                if measurement_signature() == signature:
                    score = calculate_surface_area(
                        file_path, profile_spacing_um=PROFILE_SPACING_UM,
                        profile_length_unit=PROFILE_LENGTH_UNIT,
                        expected_profiles=EXPECTED_PROFILE_COUNT,
                        min_profile_length_mm=MIN_PROFILE_LENGTH_MM,
                    )
                    if (score is not None and np.isfinite(score) and score >= 0
                            and measurement_signature() == signature):
                        measurement["surface_area_mm2"] = float(score)
                        measurement["measurement_completed_at"] = datetime.now().isoformat(timespec="milliseconds")
                        return measurement
        except (FileNotFoundError, PermissionError):
            pass  # profiler may temporarily replace/lock the file during save
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"No new complete valid profiler measurement in {file_path}; "
                "experiment was not recorded. Check output path and profile count."
            )
        time.sleep(0.2)


def run_automatic_bo(
    n_initial=N_INITIAL,
    n_bo=N_BO,
    resume_from_csv=RESUME_FROM_CSV
):

    # ========================================================
    # 1. NEW RUN or RESUME
    # ========================================================

    if resume_from_csv is None:

        # ----------------------------------------------------
        # New run
        # ----------------------------------------------------

        session_id = (
            datetime.now()
            .strftime("%Y%m%d_%H%M%S")
        )

        session_dir = (
            BASE_SAVE_DIR
            /
            f"{session_id}_{PRIOR_MODE}"
        )

        session_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        X_obs = []
        y_obs = []

        history = []

        experiment_number = 0

        n_initial_completed = 0
        n_bo_completed = 0

        print()
        print("Starting NEW optimization")

    else:

        # ----------------------------------------------------
        # Resume previous run
        # ----------------------------------------------------

        loaded = load_previous_run(
            resume_from_csv
        )

        X_obs = loaded[
            "X_obs"
        ]

        y_obs = loaded[
            "y_obs"
        ]

        history = loaded[
            "history"
        ]

        experiment_number = loaded[
            "experiment_number"
        ]

        n_initial_completed = loaded[
            "n_initial_completed"
        ]

        n_bo_completed = loaded[
            "n_bo_completed"
        ]

        session_dir = loaded[
            "session_dir"
        ]

        print()
        print(
            f"Resuming from:\n"
            f"{Path(resume_from_csv).resolve()}"
        )


    print()
    print(
        f"Save directory:\n"
        f"{session_dir.resolve()}"
    )


    print(f"BO mode: {BO_MODE}; prior: {PRIOR_MODE}; candidate policy: {COLLISION_POLICY}")
    # Initialize once, only if further physical experiments are needed.
    if n_initial_completed < n_initial or n_bo_completed < n_bo:
        from PLC_motion_controller_mod import initiate
        if not initiate():
            raise RuntimeError("PLC initialization failed; optimization stopped.")

    # ========================================================
    # 2. INITIAL LHS EXPERIMENTS
    # ========================================================

    if n_initial_completed < n_initial:

        # ----------------------------------------------------
        # Regenerate exactly the same LHS sequence
        # because RANDOM_SEED is fixed
        # ----------------------------------------------------

        initial_points = generate_initial_points(
            n=n_initial,
            seed=RANDOM_SEED
        )


        # ----------------------------------------------------
        # Safety check:
        # previous initial points should match regenerated LHS
        # ----------------------------------------------------

        if n_initial_completed > 0:

            old_initial = np.asarray(
                X_obs[:n_initial_completed]
            )

            expected_initial = initial_points[
                :n_initial_completed
            ]

            if not np.allclose(
                old_initial,
                expected_initial,
                rtol=1e-7,
                atol=1e-10
            ):

                raise ValueError(
                    "Previous initial points do not "
                    "match the current LHS settings.\n"
                    "Check RANDOM_SEED, bounds, and N_INITIAL."
                )


        print()
        print("=" * 70)
        print("INITIAL EXPERIMENTS")
        print("=" * 70)


        # ----------------------------------------------------
        # Start from the first unfinished initial point
        # ----------------------------------------------------

        for i in range(
            n_initial_completed,
            n_initial
        ):

            x = initial_points[i]

            experiment_number += 1


            print()
            print(
                f"Initial experiment "
                f"{i+1}/{n_initial}"
            )

            print(
                f"H* = {x[0]:.5f}"
            )

            print(
                f"V* = {x[1]:.5f}"
            )

            print(
                f"d* = {x[2]:.5f}  (d = {x[2] * REFERENCE_DIAMETER_MM:.5f} mm)"
            )


            if PRIOR_MODE in ("geometry", "geometry_buckling"):

                prior = get_prior_mean(
                    x.reshape(1, -1)
                )[0]

                print(
                    f"Initial mean assumption = "
                    f"{prior:.5f} mm^2"
                )


            measurement = run_automatic_experiment(x, experiment_number, phase="initial")
            y = measurement["surface_area_mm2"]


            X_obs.append(x)
            y_obs.append(y)


            best_so_far = np.max(
                y_obs
            )


            # ------------------------------------------------
            # Fit updated GP
            # ------------------------------------------------

            post_gp = None

            if len(X_obs) >= 2:

                try:

                    post_gp = fit_gp(
                        X_obs,
                        y_obs
                    )

                except Exception as e:

                    print(
                        f"GP fitting failed: {e}"
                    )

                    post_gp = None


            row = make_history_row(

                experiment_number=
                    experiment_number,

                phase="initial",
                measurement_info=measurement,

                x=x,

                measured_surface_area=y,

                best_so_far=
                    best_so_far,

                pre_gp=None,

                post_gp=post_gp,

                recommendation_info=None,

                X_after=X_obs,

                y_after=y_obs
            )


            history.append(row)


            save_history(
                history,
                session_dir,
                iteration_number=
                    experiment_number
            )


    # ========================================================
    # 3. BAYESIAN OPTIMIZATION
    # ========================================================

    print()
    print("=" * 70)
    print("BAYESIAN OPTIMIZATION")
    print("=" * 70)

    print(
        f"Completed BO iterations: "
        f"{n_bo_completed}/{n_bo}"
    )


    # --------------------------------------------------------
    # Critical part:
    #
    # if 1 BO experiment was already completed,
    # range starts from 2.
    # --------------------------------------------------------

    for bo_iteration in range(
        n_bo_completed + 1,
        n_bo + 1
    ):

        # ----------------------------------------------------
        # Reconstruct GP from ALL previous observations
        # ----------------------------------------------------

        pre_gp = fit_gp(
            X_obs,
            y_obs
        )


        # ----------------------------------------------------
        # Recommend next point
        # ----------------------------------------------------

        recommendation = suggest_next(
            pre_gp
        )


        x_next = recommendation[
            "x"
        ]


        print()
        print("=" * 70)

        print(
            f"BO iteration "
            f"{bo_iteration}/{n_bo}"
        )

        print("=" * 70)


        print(
            f"H* = {x_next[0]:.5f}"
        )

        print(
            f"V* = {x_next[1]:.5f}"
        )

        print(
            f"d* = {x_next[2]:.5f}  (d = {x_next[2] * REFERENCE_DIAMETER_MM:.5f} mm)"
        )


        if PRIOR_MODE in ("geometry", "geometry_buckling"):

            prior = get_prior_mean(
                x_next.reshape(1, -1), gp=pre_gp
            )[0]

            print(
                f"Prior mean = "
                f"{prior:.5f} mm^2"
            )


        print(
            f"Predicted surface area (mm^2) = "
            f"{recommendation['predicted_total']:.5f}"
        )

        print(
            f"Predicted std = "
            f"{recommendation['predicted_std']:.5f}"
        )

        print(
            f"UCB = "
            f"{recommendation['acquisition']:.5f}"
        )


        # ----------------------------------------------------
        # Automatic printing, profiling and scoring
        # ----------------------------------------------------

        measurement = run_automatic_experiment(x_next, experiment_number + 1, phase="BO")
        y_next = measurement["surface_area_mm2"]
        experiment_number += 1


        X_obs.append(
            x_next
        )

        y_obs.append(
            y_next
        )


        best_so_far = np.max(
            y_obs
        )


        # ----------------------------------------------------
        # Update GP after measurement
        # ----------------------------------------------------

        try:
            post_gp = fit_gp(X_obs, y_obs)
        except Exception as exc:
            warnings.warn(f"Post-measurement GP fitting failed: {exc}")
            post_gp = None


        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        row = make_history_row(

            experiment_number=
                experiment_number,

            phase="BO",
            measurement_info=measurement,

            x=x_next,

            measured_surface_area=
                y_next,

            best_so_far=
                best_so_far,

            pre_gp=
                pre_gp,

            post_gp=
                post_gp,

            recommendation_info=
                recommendation,

            X_after=
                X_obs,

            y_after=
                y_obs
        )


        history.append(row)


        main_path = save_history(

            history,

            session_dir,

            iteration_number=
                experiment_number
        )


        print()
        print(
            f"Profiler surface area (mm^2) = "
            f"{y_next:.5f}"
        )

        print(
            f"Best so far = "
            f"{best_so_far:.5f}"
        )

        print(
            f"Saved -> "
            f"{main_path}"
        )


    # ========================================================
    # 4. FINISH
    # ========================================================

    result = pd.DataFrame(
        history
    )

    print()
    print("=" * 70)
    print("OPTIMIZATION FINISHED")
    print("=" * 70)

    print(
        f"\nTotal experiments: "
        f"{len(result)}"
    )

    return result


def load_previous_run(csv_path):
    """
    Load a previous BO run and reconstruct:
        X_obs
        y_obs
        history
        number of completed initial experiments
        number of completed BO iterations
    """

    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Cannot find CSV:\n{csv_path}"
        )

    df = pd.read_csv(csv_path)
    for column, expected in {"bo_mode": BO_MODE, "collision_policy": COLLISION_POLICY,
                             "prior_mode": PRIOR_MODE}.items():
        if column not in df or not df[column].eq(expected).all():
            raise ValueError(f"Resume mode mismatch: {column}; start a new comparison run.")
    if "measurement_schema" not in df or not df["measurement_schema"].eq(MEASUREMENT_SCHEMA).all():
        raise ValueError("Old ROI/score logs cannot be resumed. Start a new run.")
    for column, value in {"reference_diameter_mm": REFERENCE_DIAMETER_MM,
                          "roi_side_mm": ARRAY_SIZE,
                          "min_profile_length_mm": MIN_PROFILE_LENGTH_MM,
                          "expected_profile_count": EXPECTED_PROFILE_COUNT,
                          "die_swelling_ratio": DIE_SWELLING_RATIO,
                          "nozzle_outer_diameter_mm": NOZZLE_OUTER_DIAMETER,
                          "collision_margin_mm": COLLISION_MARGIN_MM}.items():
        if column not in df or not np.allclose(df[column], value):
            raise ValueError(f"Resume setting mismatch: {column}")
    required = ["H_star", "V_star", "d_star", "d_mm", "measured_surface_area_mm2",
                "profiler_surface_area_mm2", "nozzle_diameter_mm", "objective_name",
                "input_schema", "profile_length_unit", "profile_spacing_um"]
    missing = [name for name in required if name not in df.columns]
    if missing or df.empty:
        raise ValueError(f"Resume requires a nonempty current-format CSV; missing: {missing}")
    if not df["objective_name"].eq(OBJECTIVE_NAME).all() or not df["input_schema"].eq(INPUT_SCHEMA).all():
        raise ValueError("Resume objective/input units differ. Start a new run for legacy data.")
    if (not np.allclose(df["nozzle_diameter_mm"], NOZZLE_DIAMETER)
            or not np.allclose(df["profile_spacing_um"], PROFILE_SPACING_UM)
            or not df["profile_length_unit"].eq(PROFILE_LENGTH_UNIT).all()):
        raise ValueError("Resume nozzle or profiler settings differ from the current run.")
    X_obs = df[["H_star", "V_star", "d_star"]].to_numpy(dtype=float)
    y_obs = df["profiler_surface_area_mm2"].to_numpy(dtype=float)
    if "phase" not in df or not df["phase"].isin(["initial", "BO"]).all():
        raise ValueError("Resume requires valid initial/BO phase labels.")
    bo_mask = df["phase"].eq("BO").to_numpy()
    if USE_NOZZLE_CLEARANCE and not collision_free(X_obs[bo_mask]).all():
        raise ValueError("Resume contains BO-phase nozzle collision configurations.")
    if (not np.isfinite(X_obs).all() or not np.isfinite(y_obs).all()
            or np.any(y_obs < 0) or np.any(X_obs < lower - 1e-9)
            or np.any(X_obs > upper + 1e-9)):
        raise ValueError("Resume observations are invalid or outside current bounds.")
    if (not np.allclose(df["d_mm"], X_obs[:, 2] * REFERENCE_DIAMETER_MM)
            or not np.allclose(df["measured_surface_area_mm2"], y_obs)):
        raise ValueError("Resume CSV contains inconsistent spacing or measured area columns.")


    # --------------------------------------------------------
    # Recover history
    # --------------------------------------------------------

    history = df.to_dict(
        orient="records"
    )


    # --------------------------------------------------------
    # Detect INITIAL / BO phases
    # --------------------------------------------------------

    if "phase" in df.columns:

        n_initial_completed = int(
            (df["phase"] == "initial").sum()
        )

        n_bo_completed = int(
            (df["phase"] == "BO").sum()
        )

    else:
        # -----------------------------------------------
        # Legacy CSV fallback:
        # assume first N_INITIAL = initial LHS
        # remaining = BO
        # -----------------------------------------------

        n_total = len(df)

        n_initial_completed = min(
            n_total,
            N_INITIAL
        )

        n_bo_completed = max(
            0,
            n_total - N_INITIAL
        )


    # --------------------------------------------------------
    # Experiment number
    # --------------------------------------------------------

    if "experiment_number" in df.columns:

        experiment_number = int(
            df["experiment_number"].max()
        )

    else:

        experiment_number = len(df)


    print()
    print("=" * 70)
    print("PREVIOUS RUN LOADED")
    print("=" * 70)

    print(
        f"Total experiments       : {len(df)}"
    )

    print(
        f"Initial experiments     : {n_initial_completed}"
    )

    print(
        f"BO experiments          : {n_bo_completed}"
    )

    print(
        f"Best surface area (mm^2): {np.max(y_obs):.5f}"
    )


    return {
        "X_obs": list(X_obs),
        "y_obs": list(y_obs),
        "history": history,
        "experiment_number": experiment_number,
        "n_initial_completed": n_initial_completed,
        "n_bo_completed": n_bo_completed,
        "session_dir": csv_path.parent,
    }





if __name__ == "__main__":
    result = run_automatic_bo(resume_from_csv=RESUME_FROM_CSV)
