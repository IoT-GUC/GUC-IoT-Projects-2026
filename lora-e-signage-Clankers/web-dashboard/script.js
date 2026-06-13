const CONFIG = { maxMessageLength: 100 };

const state = {
  connected: false,
  displays: ["DISPLAY_1", "DISPLAY_2"],
};

const elements = {
  statusDot: document.querySelector("#statusDot"),
  connectionStatus: document.querySelector("#connectionStatus"),
  targetInput: document.querySelector("#targetInput"),
  tutorialInput: document.querySelector("#tutorialInput"),
  courseInput: document.querySelector("#courseInput"),
  slotInput: document.querySelector("#slotInput"),
  roomInput: document.querySelector("#roomInput"),
  messageInput: document.querySelector("#messageInput"),
  charCount: document.querySelector("#charCount"),
  sendButton: document.querySelector("#sendButton"),
  emergencyButton: document.querySelector("#emergencyButton"),
  activityLog: document.querySelector("#activityLog"),
  clearLogButton: document.querySelector("#clearLogButton"),
  routeName: document.querySelector("#routeName"),
};

function setStatus(label, statusClass = "") {
  elements.connectionStatus.textContent = label;
  elements.statusDot.className = `status-dot ${statusClass}`.trim();
  state.connected = statusClass === "connected";
  refreshButtons();
}

function refreshButtons() {
  const hasMessage = elements.messageInput.value.trim().length > 0;
  const hasFields = [
    elements.tutorialInput,
    elements.courseInput,
    elements.slotInput,
    elements.roomInput,
  ].every((input) => input.value.trim().length > 0);
  elements.sendButton.disabled = !state.connected || !hasFields || !hasMessage;
  elements.emergencyButton.disabled = !state.connected || !hasFields || !hasMessage;
}

function addLog(kind, text) {
  const item = document.createElement("li");
  const label = document.createElement("strong");
  label.textContent = `${new Date().toLocaleTimeString()} · ${kind}`;
  item.append(label, ` ${text}`);
  elements.activityLog.prepend(item);
  while (elements.activityLog.children.length > 12) {
    elements.activityLog.lastElementChild.remove();
  }
}

function formBody() {
  return {
    tutorial: elements.tutorialInput.value,
    course: elements.courseInput.value,
    slot: elements.slotInput.value,
    room: elements.roomInput.value,
    message: elements.messageInput.value,
  };
}

async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `Request failed (${response.status})`);
  return result;
}

async function sendAnnouncement(emergency) {
  const target = elements.targetInput.value;
  const path = emergency ? "/api/emergency" : `/api/displays/${encodeURIComponent(target)}`;
  const button = emergency ? elements.emergencyButton : elements.sendButton;
  button.disabled = true;

  try {
    const result = await apiRequest(path, {
      method: emergency ? "POST" : "PUT",
      body: JSON.stringify(formBody()),
    });
    addLog(emergency ? "EMERGENCY → ALL" : `NORMAL → ${target}`, `version ${result.version}`);
    if (!emergency) elements.messageInput.value = "";
    updateCharCount();
  } catch (error) {
    addLog("Send failed", error.message);
  } finally {
    refreshButtons();
  }
}

async function checkStatus() {
  try {
    const status = await apiRequest("/api/status");
    state.displays = status.displays;
    elements.targetInput.replaceChildren(
      ...status.displays.map((display) => new Option(display, display)),
    );
    elements.routeName.textContent = status.thingsBoardUrl;
    setStatus("ThingsBoard connected", "connected");
    addLog("Connected", status.thingsBoardUrl);
  } catch (error) {
    setStatus("ThingsBoard unavailable", "error");
    addLog("Connection error", error.message);
  }
}

function updateCharCount() {
  elements.charCount.textContent = `${elements.messageInput.value.length}/${CONFIG.maxMessageLength}`;
  refreshButtons();
}

elements.messageInput.addEventListener("input", updateCharCount);
[elements.tutorialInput, elements.courseInput, elements.slotInput, elements.roomInput].forEach((input) => {
  input.addEventListener("input", refreshButtons);
});
elements.sendButton.addEventListener("click", () => sendAnnouncement(false));
elements.emergencyButton.addEventListener("click", () => sendAnnouncement(true));
elements.clearLogButton.addEventListener("click", () => elements.activityLog.replaceChildren());

updateCharCount();
checkStatus();
