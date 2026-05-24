import { StatusBar } from "expo-status-bar";
import { SafeAreaView, StyleSheet } from "react-native";
import { WebView } from "react-native-webview";

const dashboardHtml = String.raw`
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta
      name="viewport"
      content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"
    />
    <title>GUC E-Sign Mobile Admin</title>
    <script src="https://unpkg.com/mqtt/dist/mqtt.min.js"></script>
    <style>
      :root {
        color-scheme: light;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #f6f7f9;
        color: #171a21;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        background: #f6f7f9;
      }

      main {
        min-height: 100vh;
        padding: 24px 18px 34px;
      }

      h1 {
        margin: 0 0 10px;
        font-size: 28px;
        line-height: 1.14;
      }

      .status {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 18px;
        color: #3a3f49;
        font-weight: 800;
        text-transform: capitalize;
      }

      .dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #b33a3a;
      }

      .dot.connected {
        background: #178a4b;
      }

      .dot.reconnecting {
        background: #b26b00;
      }

      .dot.sending {
        background: #1d5fd1;
      }

      .metrics {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 16px;
      }

      .metric,
      textarea,
      .emergency,
      .history-item {
        border: 1px solid #dfe3ea;
        border-radius: 8px;
        background: #ffffff;
      }

      .metric {
        padding: 14px;
      }

      .metric span {
        display: block;
        color: #69707d;
        font-size: 13px;
        font-weight: 800;
      }

      .metric strong {
        display: block;
        margin-top: 4px;
        font-size: 20px;
      }

      textarea {
        width: 100%;
        min-height: 132px;
        padding: 14px;
        color: #171a21;
        font: inherit;
        font-size: 17px;
        resize: none;
        outline: none;
      }

      section {
        margin-top: 18px;
      }

      h2 {
        margin: 0 0 10px;
        font-size: 16px;
      }

      .presets {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      button {
        border: 0;
        border-radius: 8px;
        font: inherit;
        font-weight: 800;
      }

      .preset {
        border: 1px solid #cfd5df;
        background: #ffffff;
        color: #252a34;
        padding: 10px 12px;
      }

      .emergency {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        margin-top: 18px;
        padding: 14px;
        border-color: #ead1d1;
      }

      .emergency-title {
        display: block;
        color: #9d2727;
        font-size: 17px;
        font-weight: 900;
      }

      .emergency-subtitle {
        display: block;
        margin-top: 3px;
        color: #686f7b;
        font-size: 13px;
        font-weight: 700;
      }

      input[type="checkbox"] {
        width: 42px;
        height: 42px;
        accent-color: #d94b4b;
      }

      .error {
        min-height: 20px;
        margin: 12px 0 8px;
        color: #a12626;
        font-size: 14px;
        font-weight: 800;
      }

      .send {
        width: 100%;
        min-height: 54px;
        background: #1f6f4a;
        color: #ffffff;
        font-size: 18px;
      }

      .send:disabled {
        background: #9aa3ad;
      }

      .empty {
        color: #6c737f;
        font-weight: 700;
      }

      .history-list {
        display: grid;
        gap: 10px;
      }

      .history-item {
        padding: 12px;
      }

      .history-item strong {
        display: block;
        font-size: 15px;
        overflow-wrap: anywhere;
      }

      .history-item span {
        display: block;
        margin-top: 6px;
        color: #707884;
        font-size: 12px;
        font-weight: 800;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>GUC E-Sign Mobile Admin</h1>

      <div class="status">
        <div id="dot" class="dot"></div>
        <span id="statusText">disconnected</span>
      </div>

      <div class="metrics">
        <div class="metric">
          <span>Sent</span>
          <strong id="sentCount">0</strong>
        </div>
        <div class="metric">
          <span>Last sent</span>
          <strong id="lastSent">None</strong>
        </div>
      </div>

      <textarea
        id="messageInput"
        placeholder="Type announcement for campus display boards"
      ></textarea>

      <section>
        <h2>Presets</h2>
        <div class="presets" id="presets"></div>
      </section>

      <label class="emergency">
        <span>
          <span class="emergency-title">Emergency</span>
          <span class="emergency-subtitle">
            Prefixes the publish payload with EMERGENCY:
          </span>
        </span>
        <input id="emergencyInput" type="checkbox" />
      </label>

      <div id="errorText" class="error"></div>

      <button id="sendButton" class="send" disabled>Send</button>

      <section>
        <h2>Last Sent Messages</h2>
        <div id="historyList" class="history-list">
          <div class="empty">No messages sent yet.</div>
        </div>
      </section>
    </main>

    <script>
      const BROKER = "wss://broker.hivemq.com:8884/mqtt";
      const TOPIC = "guc/datasignage/display";
      const PRESETS = [
        "Class cancelled",
        "Room changed to H7",
        "Meeting at 2PM",
        "Office hours open",
        "Lab closed today"
      ];

      const state = {
        client: null,
        status: "disconnected",
        sending: false,
        history: []
      };

      const dot = document.getElementById("dot");
      const statusText = document.getElementById("statusText");
      const messageInput = document.getElementById("messageInput");
      const emergencyInput = document.getElementById("emergencyInput");
      const errorText = document.getElementById("errorText");
      const sendButton = document.getElementById("sendButton");
      const historyList = document.getElementById("historyList");
      const sentCount = document.getElementById("sentCount");
      const lastSent = document.getElementById("lastSent");
      const presets = document.getElementById("presets");

      PRESETS.forEach((preset) => {
        const button = document.createElement("button");
        button.className = "preset";
        button.type = "button";
        button.textContent = preset;
        button.addEventListener("click", () => {
          messageInput.value = preset;
          errorText.textContent = "";
          render();
        });
        presets.appendChild(button);
      });

      function connectMqtt() {
        if (!window.mqtt) {
          setStatus("disconnected");
          errorText.textContent = "MQTT script did not load. Check internet.";
          return;
        }

        const clientId = "guc-mobile-admin-" + Date.now() + "-" +
          Math.random().toString(16).slice(2);

        state.client = mqtt.connect(BROKER, {
          clientId,
          clean: true,
          reconnectPeriod: 3000
        });

        state.client.on("connect", () => {
          setStatus("connected");
          errorText.textContent = "";
        });

        state.client.on("reconnect", () => setStatus("reconnecting"));
        state.client.on("offline", () => setStatus("disconnected"));
        state.client.on("close", () => {
          if (state.status === "connected") {
            setStatus("reconnecting");
          }
        });
        state.client.on("error", (error) => {
          setStatus("disconnected");
          errorText.textContent = error && error.message
            ? error.message
            : "MQTT connection error";
        });
      }

      function setStatus(status) {
        state.status = status;
        render();
      }

      function render() {
        const displayStatus = state.sending ? "sending" : state.status;
        dot.className = "dot " + displayStatus;
        statusText.textContent = displayStatus;
        sentCount.textContent = state.history.length;
        lastSent.textContent = state.history[0] ? state.history[0].time : "None";
        sendButton.disabled =
          state.sending ||
          state.status !== "connected" ||
          messageInput.value.trim().length === 0;

        if (!state.history.length) {
          historyList.innerHTML = '<div class="empty">No messages sent yet.</div>';
          return;
        }

        historyList.innerHTML = state.history
          .map((item) => (
            '<div class="history-item"><strong>' +
            escapeHtml(item.payload) +
            '</strong><span>' +
            item.time +
            '</span></div>'
          ))
          .join("");
      }

      function publishMessage() {
        const typedMessage = messageInput.value.trim();

        if (!typedMessage) {
          errorText.textContent = "Type a message before sending.";
          render();
          return;
        }

        if (state.status !== "connected" || !state.client) {
          errorText.textContent = "MQTT is not connected yet.";
          render();
          return;
        }

        const payload = emergencyInput.checked
          ? "EMERGENCY:" + typedMessage
          : typedMessage;

        state.sending = true;
        errorText.textContent = "";
        render();

        state.client.publish(TOPIC, payload, { qos: 0 }, (error) => {
          state.sending = false;

          if (error) {
            errorText.textContent = error.message || "Publish failed. Try again.";
            render();
            return;
          }

          const time = new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit"
          });

          messageInput.value = "";
          state.history = [{ payload, time }, ...state.history].slice(0, 6);
          render();
        });
      }

      function escapeHtml(value) {
        return value.replace(/[&<>"']/g, (character) => ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#039;"
        }[character]));
      }

      messageInput.addEventListener("input", () => {
        errorText.textContent = "";
        render();
      });
      emergencyInput.addEventListener("change", render);
      sendButton.addEventListener("click", publishMessage);

      render();
      connectMqtt();
    </script>
  </body>
</html>
`;

export default function App() {
  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      <WebView
        originWhitelist={["*"]}
        source={{ html: dashboardHtml, baseUrl: "https://localhost" }}
        javaScriptEnabled
        domStorageEnabled
        startInLoadingState
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#f6f7f9"
  }
});
