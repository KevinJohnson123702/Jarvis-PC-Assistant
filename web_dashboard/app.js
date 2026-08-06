async function getStatus() {
    try {
        const response = await fetch("http://192.168.56.1:8000/status");
        const data = await response.json();

        document.getElementById("status").innerHTML =
            `
            <p>🟢 ${data.status}</p>
            <p>💻 ${data.computer}</p>
            <p>CPU: ${data.cpu}%</p>
            <p>RAM: ${data.ram}%</p>
            `;
    } catch (error) {
        document.getElementById("status").innerHTML =
            "🔴 Could not connect to Jarvis.";
    }
}

getStatus();
