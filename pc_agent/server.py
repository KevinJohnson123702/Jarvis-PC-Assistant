from fastapi import FastAPI
import socket
import psutil

app = FastAPI()

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
