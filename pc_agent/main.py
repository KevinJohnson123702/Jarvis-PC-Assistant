import os
import sys
import subprocess


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

VOICE_FILE = os.path.join(
    BASE_DIR,
    "voice.py"
)


print("Jarvis is starting...")


try:
    subprocess.run(
        [
            sys.executable,
            VOICE_FILE
        ],
        cwd=BASE_DIR
    )

except KeyboardInterrupt:
    print("\nJarvis shutting down...")

except Exception as e:
    print(
        "Jarvis error:",
        e
    )
