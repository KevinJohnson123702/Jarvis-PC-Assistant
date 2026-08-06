import speech_recognition as sr
import pyttsx3
import sounddevice as sd
import numpy as np
import wave


engine = pyttsx3.init()


def speak(text):
    print("Jarvis:", text)
    engine.say(text)
    engine.runAndWait()


def record_audio(filename="voice.wav", duration=5, samplerate=44100):

    print("🎤 Listening...")

    recording = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    with wave.open(filename, "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(samplerate)
        file.writeframes(recording.tobytes())


def listen():

    filename = "voice.wav"

    record_audio(filename)


    recognizer = sr.Recognizer()

    with sr.AudioFile(filename) as source:

        audio = recognizer.record(source)


    try:

        command = recognizer.recognize_google(audio)

        print("You:", command)

        return command.lower()


    except Exception:

        return ""


def start_voice():

    speak("Jarvis is online.")

    while True:

        command = listen()


        if "jarvis wake up" in command:

            speak("Online. What do you need?")


if __name__ == "__main__":
    start_voice()
