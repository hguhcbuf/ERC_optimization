import torch
import pandas as pd

# 1) 로드 ──────────────────────────────────────────────
ckpt_path = r"C:\Users\Administrator\Documents\JH\optimization_logs\MOBO_qNEHVI_20250619_023619.pt"
ckpt      = torch.load(ckpt_path, map_location="cpu")   # GPU에서 저장했어도 map_location="cpu"면 OK

X_raw = ckpt["X_raw"]     # shape: (N, 5)
Y     = ckpt["Y"]         # shape: (N, 2)

# 2) 텐서를 넘파이/판다스로 변환 ───────────────────────
df_X = pd.DataFrame(
    X_raw.numpy(),
    columns=[
        "inter_layer_standoff",
        "n_ligaments",
        "line_velocity",
        "num_layers",
        "pressure",
    ],
)
df_Y = pd.DataFrame(Y.numpy(), columns=["score1", "score2"])

df = pd.concat([df_X, df_Y], axis=1)
print(df.head())

# 3) CSV로 저장하고 싶다면
csv_path = ckpt_path.replace(".pt", ".csv")
df.to_csv(csv_path, index=False)
print("저장 완료 →", csv_path)
