import uvicorn
import threading
import time


def start_voice():

    import voice

    voice.start_voice()


def run_voice():

    time.sleep(2)

    start_voice()


print("Jarvis is starting...")


voice_thread = threading.Thread(
    target=run_voice,
    daemon=True
)

voice_thread.start()


uvicorn.run(
    "server:app",
    host="0.0.0.0",
    port=8000
)
