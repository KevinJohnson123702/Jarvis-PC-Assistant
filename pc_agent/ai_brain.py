"""Local AI conversation layer for Jarvis.

Uses Ollama's local HTTP API. Install Ollama and pull a small model such as
qwen2.5:3b or llama3.2:3b, then Jarvis can use this module without cloud APIs.
"""

import json
import urllib.error
import urllib.request

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen2.5:3b"
SYSTEM_PROMPT = (
    "You are Jarvis, a concise, helpful local PC assistant. "
    "Speak naturally and conversationally. Do not claim to have performed "
    "computer actions unless Jarvis's command system actually performed them. "
    "Keep voice responses reasonably short unless the user asks for detail."
)

_history = []


def reset_conversation():
    global _history
    _history = []


def is_available(timeout=1.5):
    try:
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/tags",
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=timeout):
            return True
    except (OSError, urllib.error.URLError):
        return False


def ask(prompt, timeout=90):
    global _history

    prompt = prompt.strip()
    if not prompt:
        return ""

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(_history[-10:])
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.7,
        },
    }).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        answer = data.get("message", {}).get("content", "").strip()
        if not answer:
            return "I didn't get a response from my local AI brain."

        _history.append({"role": "user", "content": prompt})
        _history.append({"role": "assistant", "content": answer})
        _history = _history[-10:]
        return answer

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return f"My local AI model '{MODEL}' is not installed yet."
        return f"My local AI brain returned an HTTP error: {e.code}."
    except (OSError, urllib.error.URLError):
        return "My local AI brain is offline. Start Ollama and try again."
    except Exception as e:
        print("AI error:", e)
        return "I hit an error while thinking."
