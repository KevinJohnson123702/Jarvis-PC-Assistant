from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import socket
import psutil
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/dashboard",
    StaticFiles(directory="../web_dashboard", html=True),
    name="dashboard"
)

start_time = time.time()


@app.get("/")
def home():
    return {
        "name": "Jarvis",
        "status": "online"
    }


@app.get("/status")
def status():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    uptime_seconds = int(time.time() - start_time)

    return {
        "computer": socket.gethostname(),
        "cpu": psutil.cpu_percent(),
        "cpu_cores": psutil.cpu_count(),
        "ram": memory.percent,
        "ram_total": round(memory.total / (1024**3), 2),
        "storage": disk.percent,
        "uptime": uptime_seconds,
        "status": "online"
    }
