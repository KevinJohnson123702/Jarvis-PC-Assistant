const JARVIS_URL = "http://192.168.1.12:8000";


async function getStatus() {
    const statusBox = document.getElementById("status");

    try {
        const response = await fetch(`${JARVIS_URL}/status`);
        const data = await response.json();

        const uptimeHours = Math.floor(data.uptime / 3600);
        const uptimeMinutes = Math.floor((data.uptime % 3600) / 60);

        statusBox.innerHTML = `
            <h2>🟢 Jarvis Online</h2>

            <p>💻 Computer: ${data.computer}</p>

            <hr>

            <p>⚙️ CPU Usage: ${data.cpu}%</p>
            <p>🧩 CPU Cores: ${data.cpu_cores}</p>

            <p>🧠 RAM Usage: ${data.ram}%</p>
            <p>💾 Total RAM: ${data.ram_total} GB</p>

            <p>📦 Storage Used: ${data.storage}%</p>

            <p>⏱️ Uptime: ${uptimeHours}h ${uptimeMinutes}m</p>
        `;

    } catch (error) {

        statusBox.innerHTML = `
            <h2>🔴 Jarvis Offline</h2>
            <p>${error}</p>
        `;
    }
}


async function command(action) {

    alert("Sending command: " + action);

    try {

        const response = await fetch(
            `${JARVIS_URL}/${action}`,
            {
                method: "POST"
            }
        );

        const data = await response.json();

        alert("🤖 Jarvis: " + data.status);

    } catch (error) {

        alert("🔴 Command failed: " + error);

    }
}


window.onload = function() {
    getStatus();
};
