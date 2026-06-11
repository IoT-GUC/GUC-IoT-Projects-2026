const http = require("node:http");
const fs = require("node:fs/promises");
const path = require("node:path");

loadEnv(path.join(__dirname, ".env"));

const config = {
  port: Number(process.env.PORT || 8080),
  thingsBoardUrl: (process.env.THINGSBOARD_URL || "https://demo.thingsboard.io").replace(/\/$/, ""),
  username: process.env.THINGSBOARD_USERNAME || "",
  password: process.env.THINGSBOARD_PASSWORD || "",
  jwt: process.env.THINGSBOARD_JWT || "",
  displays: [
    process.env.DISPLAY_1_NAME || "DISPLAY_1",
    process.env.DISPLAY_2_NAME || "DISPLAY_2",
  ],
};

const publicFiles = new Map([
  ["/", ["index.html", "text/html; charset=utf-8"]],
  ["/index.html", ["index.html", "text/html; charset=utf-8"]],
  ["/styles.css", ["styles.css", "text/css; charset=utf-8"]],
  ["/script.js", ["script.js", "text/javascript; charset=utf-8"]],
]);

let authToken = "";
let authExpiresAt = 0;
const deviceIds = new Map();

function loadEnv(filename) {
  try {
    const content = require("node:fs").readFileSync(filename, "utf8");
    for (const line of content.split(/\r?\n/)) {
      const match = line.match(/^\s*([^#=\s]+)\s*=\s*(.*)\s*$/);
      if (!match || process.env[match[1]] !== undefined) continue;
      process.env[match[1]] = match[2].replace(/^(['"])(.*)\1$/, "$2");
    }
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
}

function sendJson(response, status, body) {
  response.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(body));
}

async function readJson(request) {
  let body = "";
  for await (const chunk of request) {
    body += chunk;
    if (body.length > 16_384) throw new Error("Request body is too large.");
  }
  return body ? JSON.parse(body) : {};
}

function sanitize(value, maxLength) {
  return String(value ?? "")
    .replace(/[|\r\n]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, maxLength);
}

function validateAnnouncement(body, priority) {
  const announcement = {
    tutorial: sanitize(body.tutorial, 12),
    course: sanitize(body.course, 24),
    slot: sanitize(body.slot, 20),
    room: sanitize(body.room, 16),
    message: sanitize(body.message, 100),
    priority,
  };

  for (const [key, value] of Object.entries(announcement)) {
    if (!value) throw new Error(`${key} is required.`);
  }
  const maximumPacketLength =
    85
    + announcement.tutorial.length
    + announcement.course.length
    + announcement.slot.length
    + announcement.room.length
    + announcement.message.length
    + announcement.priority.length;
  if (maximumPacketLength > 240) {
    throw new Error("The combined fields are too long for one LoRa packet.");
  }
  return announcement;
}

async function tbFetch(endpoint, options = {}, retry = true) {
  if (!authToken || Date.now() >= authExpiresAt) await authenticate();
  const response = await fetch(`${config.thingsBoardUrl}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Authorization": `Bearer ${authToken}`,
      ...options.headers,
    },
  });

  if (response.status === 401 && retry) {
    authToken = "";
    return tbFetch(endpoint, options, false);
  }
  if (!response.ok) {
    throw new Error(`ThingsBoard ${response.status}: ${await response.text()}`);
  }
  if (response.status === 204) return null;
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

async function authenticate() {
  if (config.jwt) {
    const payload = JSON.parse(Buffer.from(config.jwt.split(".")[1], "base64url").toString("utf8"));
    authToken = config.jwt;
    authExpiresAt = Number(payload.exp || 0) * 1000;
    if (Date.now() >= authExpiresAt) {
      throw new Error("The ThingsBoard JWT has expired. Replace THINGSBOARD_JWT in .env.");
    }
    return;
  }

  if (!config.username || !config.password) {
    throw new Error("Configure either THINGSBOARD_JWT or ThingsBoard username/password in .env.");
  }
  const response = await fetch(`${config.thingsBoardUrl}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: config.username, password: config.password }),
  });
  if (!response.ok) throw new Error(`ThingsBoard login failed (${response.status}).`);

  const result = await response.json();
  authToken = result.token;
  authExpiresAt = Date.now() + 50 * 60 * 1000;
}

async function getDeviceId(deviceName) {
  if (deviceIds.has(deviceName)) return deviceIds.get(deviceName);
  const device = await tbFetch(`/api/tenant/devices?deviceName=${encodeURIComponent(deviceName)}`);
  if (!device?.id?.id) throw new Error(`ThingsBoard device "${deviceName}" was not found.`);
  deviceIds.set(deviceName, device.id.id);
  return device.id.id;
}

async function getDisplayState(deviceName) {
  const id = await getDeviceId(deviceName);
  const attributes = await tbFetch(`/api/plugins/telemetry/DEVICE/${id}/values/attributes/SHARED_SCOPE`);
  return Object.fromEntries((attributes || []).map(({ key, value }) => [key, value]));
}

async function saveDisplayState(deviceName, values) {
  const id = await getDeviceId(deviceName);
  await tbFetch(`/api/plugins/telemetry/DEVICE/${id}/attributes/SHARED_SCOPE`, {
    method: "POST",
    body: JSON.stringify(values),
  });
}

async function nextVersion(deviceNames) {
  const states = await Promise.all(deviceNames.map(getDisplayState));
  return Math.max(0, ...states.map((state) => Number(state.version) || 0)) + 1;
}

async function syncDisplayStates() {
  for (const deviceName of config.displays) {
    const state = await getDisplayState(deviceName);
    if (Object.keys(state).length > 0) {
      await saveDisplayState(deviceName, state);
    }
  }
  console.log("Republished display states for the ThingsBoard MQTT gateway.");
}

async function handleApi(request, response, url) {
  if (request.method === "GET" && url.pathname === "/api/status") {
    try {
      await authenticate();
      return sendJson(response, 200, {
        connected: true,
        thingsBoardUrl: config.thingsBoardUrl,
        displays: config.displays,
      });
    } catch (error) {
      return sendJson(response, 503, { connected: false, error: error.message });
    }
  }

  if (request.method === "GET" && url.pathname === "/api/displays") {
    const states = await Promise.all(
      config.displays.map(async (deviceId) => ({ deviceId, ...(await getDisplayState(deviceId)) })),
    );
    return sendJson(response, 200, states);
  }

  const displayMatch = url.pathname.match(/^\/api\/displays\/([^/]+)$/);
  if (request.method === "PUT" && displayMatch) {
    const deviceId = decodeURIComponent(displayMatch[1]);
    if (!config.displays.includes(deviceId)) throw new Error("Unknown display target.");
    const announcement = validateAnnouncement(await readJson(request), "NORMAL");
    const version = await nextVersion([deviceId]);
    await saveDisplayState(deviceId, { ...announcement, version });
    return sendJson(response, 200, { deviceId, ...announcement, version });
  }

  if (request.method === "POST" && url.pathname === "/api/emergency") {
    const announcement = validateAnnouncement(await readJson(request), "EMERGENCY");
    const version = await nextVersion(config.displays);
    await Promise.all(config.displays.map((deviceId) => saveDisplayState(deviceId, {
      ...announcement,
      room: "ALL",
      version,
    })));
    return sendJson(response, 200, {
      targets: config.displays,
      ...announcement,
      room: "ALL",
      version,
    });
  }

  sendJson(response, 404, { error: "API route not found." });
}

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url, `http://${request.headers.host || "localhost"}`);
  try {
    if (url.pathname.startsWith("/api/")) {
      await handleApi(request, response, url);
      return;
    }

    const publicFile = publicFiles.get(url.pathname);
    if (!publicFile) {
      response.writeHead(404);
      response.end("Not found");
      return;
    }
    const [filename, contentType] = publicFile;
    response.writeHead(200, { "Content-Type": contentType });
    response.end(await fs.readFile(path.join(__dirname, filename)));
  } catch (error) {
    console.error(error);
    sendJson(response, 500, { error: error.message || "Unexpected server error." });
  }
});

server.listen(config.port, "0.0.0.0", () => {
  console.log(`Dashboard: http://localhost:${config.port}`);
  console.log(`ThingsBoard: ${config.thingsBoardUrl}`);
  console.log(`Displays: ${config.displays.join(", ")}`);

  setTimeout(() => {
    syncDisplayStates().catch((error) => console.error("Initial display sync failed:", error.message));
  }, 2000);

  setInterval(() => {
    syncDisplayStates().catch((error) => console.error("Periodic display sync failed:", error.message));
  }, 30000);
});
