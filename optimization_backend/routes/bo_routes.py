from fastapi import APIRouter, HTTPException
import torch
from models.schemas import BatchResult, BOConfig, Measurement
from services import bo_service
from fastapi.responses import StreamingResponse
import asyncio

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



#----------------------------------------------------------------------선 최적화 임시 구현-----------------------------------------------------

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from services.printing_service import print_line_by_iter
from services.pressure_service import NordsonEFD
from services.calculate_score import calculate_area_error
from bayes_opt import BayesianOptimization
import threading, asyncio, json, os

# … inst, print_line_by_iter, calculate_area_error 등은 그대로 …

file_path = r"C:\FTP\Keyence\lj-s\result\SD1_004\250623_070250.txt"
log_dir   = r"C:\Users\Administrator\Documents\JH\optimization_logs"
os.makedirs(log_dir, exist_ok=True)

inst = NordsonEFD(port="COM5", baudrate=115200, timeout=1)
origin_z = 15

count           = 1
results_to_send = []
running         = False
finished_evt    = threading.Event()          # ★ BO 완료 신호

@router.post("/line_reset")
async def resetState():
    global count, results_to_send
    results_to_send.clear()
    count = 1
    print("🔄 optimization state reset")
    return {"status": "ok"}

@router.get("/run_optimization")
async def run_optimization(request: Request):
    global running
    if running:
        return StreamingResponse(
            iter([b"event: busy\ndata: 1\n\n"]),
            media_type="text/event-stream"
        )
    running = True
    finished_evt.clear()                     # ★ 새 실행이므로 리셋

    # ── Black-box ------------------------------------------
    def black_box_function(standoff_distance, line_velocity, pressure):
        global count
        standoff_distance = round(standoff_distance, 3)
        line_velocity     = round(line_velocity,   3)
        pressure          = round(pressure,        3)

        inst.SetPressure(pressure)
        print_line_by_iter(count, origin_z, standoff_distance, line_velocity)
        score = calculate_area_error(file_path, 0.1)

        results_to_send.append({
            "iter"             : count,
            "standoff_distance": standoff_distance,
            "line_velocity"    : line_velocity,
            "pressure"         : pressure,
            "score"            : score,
        })
        count += 1
        return -score
    # -------------------------------------------------------

    optimizer = BayesianOptimization(
        f       = black_box_function,
        pbounds = {
            "standoff_distance": (0.1, 0.5),
            "line_velocity"    : (2, 40),
            "pressure"         : (250, 450),
        },
        verbose = 0,
    )

    def run_bo():
        optimizer.maximize(init_points=10, n_iter=40)
        finished_evt.set()                   # ★ BO 끝!
        print("✅ BO finished")

    threading.Thread(target=run_bo, daemon=True).start()

    async def sse():
        sent = 0
        while True:
            await asyncio.sleep(0.2)
            if await request.is_disconnected():
                print("🛑 client disconnected")
                break

            # 새 결과 flush
            while sent < len(results_to_send):
                data = json.dumps(results_to_send[sent])
                print(f"📤 {data}")
                sent += 1
                yield f"data: {data}\n\n"

            # BO 끝났고 모든 데이터 보냈으면 close 이벤트
            if finished_evt.is_set() and sent >= len(results_to_send):
                yield "event: close\ndata: bye\n\n"
                break

        running = False                      # ★ 다시 실행 가능
        print("🌙 SSE generator closed")

    return StreamingResponse(sse(), media_type="text/event-stream")

