from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import bo_routes
from routes import jogger_routes
from routes import image_routes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bo_routes.router)
app.include_router(jogger_routes.router, prefix="/jogger")
app.include_router(image_routes.router, prefix="/image")