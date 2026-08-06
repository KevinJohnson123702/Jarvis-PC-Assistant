const JARVIS_URL = "http://192.168.1.12:8000";

async function getStatus() {
    const statusBox = document.getElementById("status");

    try {
        statusBox.innerHTML = "Connecting to Jarvis... 🤖";

        const response = await fetch(`${JARVIS_URL}/status`);

        if (!response.ok) {
            throw new Error("Server error: " + response.status);
        }

        const data = await response.json();

        statusBox.innerHTML = `
            <h2>🟢 Jarvis Online</h2>
            <p>💻 Computer: ${data.computer}</p>
            <p>⚙️ CPU: ${data.cpu}%</p>
            <p>🧠 RAM: ${data.ram}%</p>
        `;

    } catch (error) {
        statusBox.innerHTML = `
            <h2>🔴 Jarvis Offline</h2>
            <p>${error.message}</p>
        `;
    }
}

getStatus();
