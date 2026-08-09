from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import socket
import psutil
import time

from actions import (
    lock_pc,
    shutdown_pc,
    restart_pc,
    take_screenshot,
    open_discord,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/dashboard",
    StaticFiles(directory="../web_dashboard", html=True),
    name="dashboard",
)

start_time = time.time()


@app.get("/")
def home():
    return {"name": "Jarvis", "status": "online"}


@app.get("/status")
def status():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "computer": socket.gethostname(),
        "cpu": psutil.cpu_percent(),
        "cpu_cores": psutil.cpu_count(),
        "ram": memory.percent,
        "ram_total": round(memory.total / (1024**3), 2),
        "storage": disk.percent,
        "uptime": int(time.time() - start_time),
        "status": "online",
    }


@app.post("/lock")
def lock():
    return lock_pc()


@app.post("/shutdown")
def shutdown():
    return shutdown_pc()


@app.post("/restart")
def restart():
    return restart_pc()


@app.post("/screenshot")
def screenshot():
    return take_screenshot()


@app.post("/discord")
def discord():
    return open_discord()
