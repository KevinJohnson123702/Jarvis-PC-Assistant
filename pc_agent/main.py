import os
import sys
import subprocess
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOICE_FILE = os.path.join(BASE_DIR, "voice.py")
SERVER_FILE = os.path.join(BASE_DIR, "server.py")


def start_server():
    """Start the Jarvis dashboard/API on the local network only."""
    try:
        import uvicorn

        print("Starting Jarvis dashboard on port 8000...")
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="warning",
        )
    except Exception as e:
        print("Dashboard error:", e)


print("Jarvis is starting...")

# Run the dashboard/API in the background so the voice assistant can use
# the same main.py process. Binding to 0.0.0.0 makes it reachable from
# other devices on the same Wi-Fi, but does not create router port forwarding.
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

try:
    subprocess.run(
        [sys.executable, VOICE_FILE],
        cwd=BASE_DIR,
    )
except KeyboardInterrupt:
    print("\nJarvis shutting down...")
except Exception as e:
    print("Jarvis error:", e)
