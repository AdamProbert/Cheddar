const statusBox = () => document.getElementById("status");

function setStatus(message, kind = "info") {
    const box = statusBox();
    if (!box) return;
    box.textContent = message;
    box.dataset.kind = kind;
}

async function postJson(path, payload = {}) {
    const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.status !== "ok") {
        const detail = data?.detail || response.statusText;
        throw new Error(detail || "Request failed");
    }
    return data;
}

function createServoControls() {
    const container = document.getElementById("servo-controls");
    if (!container) return;

    for (let channel = 0; channel < 6; channel += 1) {
        const card = document.createElement("div");
        card.className = "servo-card";

        const title = document.createElement("h3");
        title.textContent = `Servo ${channel}`;
        card.appendChild(title);

        const slider = document.createElement("input");
        slider.type = "range";
        slider.min = "500";
        slider.max = "2500";
        slider.step = "10";
        slider.value = "1500";

        const valueLabel = document.createElement("div");
        valueLabel.className = "value";
        valueLabel.textContent = `${slider.value} μs`;

        slider.addEventListener("input", () => {
            valueLabel.textContent = `${slider.value} μs`;
        });

        const button = document.createElement("button");
        button.textContent = "Set Pulse";
        button.className = "primary";
        button.addEventListener("click", async () => {
            try {
                setStatus(`Setting servo ${channel} to ${slider.value} μs…`);
                const data = await postJson("/api/servo", {
                    channel,
                    pulse_us: Number.parseInt(slider.value, 10),
                });
                setStatus(`Servo ${channel} updated (${data.response}).`, "success");
            } catch (error) {
                setStatus(`Servo ${channel} failed: ${error.message}`, "error");
            }
        });

        card.appendChild(slider);
        card.appendChild(valueLabel);
        card.appendChild(button);
        container.appendChild(card);
    }
}

function bindMotorForm() {
    const form = document.getElementById("motor-form");
    const targetEl = document.getElementById("motor-target");
    const directionEl = document.getElementById("motor-direction");
    const speedEl = document.getElementById("motor-speed");
    const speedLabel = document.getElementById("motor-speed-value");

    if (!form || !targetEl || !directionEl || !speedEl || !speedLabel) return;

    speedEl.addEventListener("input", () => {
        speedLabel.textContent = Number.parseFloat(speedEl.value).toFixed(2);
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const payload = {
            target: targetEl.value,
            direction: directionEl.value,
            speed: Number.parseFloat(speedEl.value),
        };
        try {
            setStatus(`Running motor ${payload.target} ${payload.direction.toLowerCase()} at ${payload.speed.toFixed(2)}…`);
            const data = await postJson("/api/motor/run", payload);
            setStatus(`Motor command accepted (${data.response}).`, "success");
        } catch (error) {
            setStatus(`Motor run failed: ${error.message}`, "error");
        }
    });

    document.getElementById("motor-start")?.addEventListener("click", async () => {
        const target = targetEl.value;
        try {
            setStatus(`Starting motor ${target}…`);
            const data = await postJson("/api/motor/start", { target });
            setStatus(`Motor start accepted (${data.response}).`, "success");
        } catch (error) {
            setStatus(`Motor start failed: ${error.message}`, "error");
        }
    });

    document.getElementById("motor-stop")?.addEventListener("click", async () => {
        const target = targetEl.value;
        try {
            setStatus(`Stopping motor ${target}…`);
            const data = await postJson("/api/motor/stop", { target });
            setStatus(`Motor stop accepted (${data.response}).`, "success");
        } catch (error) {
            setStatus(`Motor stop failed: ${error.message}`, "error");
        }
    });
}

function bindSweepAndLogControls() {
    const sweepRange = document.getElementById("sweep-range");

    document.getElementById("sweep-enable")?.addEventListener("click", async () => {
        try {
            const rangeToken = sweepRange?.value.trim() || undefined;
            setStatus(`Enabling sweep${rangeToken ? ` (${rangeToken})` : ""}…`);
            const data = await postJson("/api/sweep", { enabled: true, sweep_range: rangeToken });
            setStatus(`Sweep enabled (${data.response}).`, "success");
        } catch (error) {
            setStatus(`Enable sweep failed: ${error.message}`, "error");
        }
    });

    document.getElementById("sweep-disable")?.addEventListener("click", async () => {
        try {
            const rangeToken = sweepRange?.value.trim() || undefined;
            setStatus(`Disabling sweep${rangeToken ? ` (${rangeToken})` : ""}…`);
            const data = await postJson("/api/sweep", { enabled: false, sweep_range: rangeToken });
            setStatus(`Sweep disabled (${data.response}).`, "success");
        } catch (error) {
            setStatus(`Disable sweep failed: ${error.message}`, "error");
        }
    });

    document.getElementById("log-enable")?.addEventListener("click", async () => {
        try {
            setStatus("Enabling telemetry logging…");
            const data = await postJson("/api/log", { enabled: true });
            setStatus(`Telemetry enabled (${data.response}).`, "success");
        } catch (error) {
            setStatus(`Enable telemetry failed: ${error.message}`, "error");
        }
    });

    document.getElementById("log-disable")?.addEventListener("click", async () => {
        try {
            setStatus("Disabling telemetry logging…");
            const data = await postJson("/api/log", { enabled: false });
            setStatus(`Telemetry disabled (${data.response}).`, "success");
        } catch (error) {
            setStatus(`Disable telemetry failed: ${error.message}`, "error");
        }
    });
}

function bindPing() {
    document.getElementById("ping")?.addEventListener("click", async () => {
        try {
            setStatus("Sending PING…");
            const data = await postJson("/api/ping");
            setStatus(`Device responded: ${data.response}`, "success");
        } catch (error) {
            setStatus(`PING failed: ${error.message}`, "error");
        }
    });
}

window.addEventListener("DOMContentLoaded", () => {
    createServoControls();
    bindMotorForm();
    bindSweepAndLogControls();
    bindPing();
    setStatus("Ready.");
});
