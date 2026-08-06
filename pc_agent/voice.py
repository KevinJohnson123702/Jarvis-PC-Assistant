def handle_command(command):

    if "calculator" in command:

        speak("Opening calculator.")

        open_calculator()


    elif "screenshot" in command:

        speak("Taking screenshot.")

        take_screenshot()


    elif "lock computer" in command or "lock pc" in command:

        speak("Locking computer.")

        lock_pc()


    elif "back" in command and "black" in command:

        speak("Playing Back in Black.")

        import webbrowser

        webbrowser.open(
            "https://open.spotify.com/search/AC%20DC%20Back%20in%20Black"
        )


    else:

        speak("I did not understand that command.")
