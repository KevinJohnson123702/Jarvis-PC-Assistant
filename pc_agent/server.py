from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socket
import psutil

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "name": "Jarvis",
        "status": "online"
    }

@app.get("/status")
def status():
    return {
        "computer": socket.gethostname(),
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "status": "online"
    }
