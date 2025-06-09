from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import bo_routes
from routes import pressure_routes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bo_routes.router)
app.include_router(pressure_routes.router, prefix="/pressure")