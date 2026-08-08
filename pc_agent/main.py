import subprocess
import sys
import os


print("Jarvis is starting...")


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


voice_path = os.path.join(
    BASE_DIR,
    "voice.py"
)


try:

    subprocess.run(
        [
            sys.executable,
            voice_path
        ],
        cwd=BASE_DIR
    )


except KeyboardInterrupt:

    print("\nJarvis shutting down...")


except Exception as e:

    print(
        f"Jarvis error: {e}"
    )
