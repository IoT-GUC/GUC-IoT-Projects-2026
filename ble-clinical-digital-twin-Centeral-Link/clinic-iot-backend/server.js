require('dotenv').config();
const env = process.env;
const express = require('express');
const cors = require('cors');
const db = require('./services/oracle-db');
const authMiddleware = require('./middleware/auth');

// Configuration
const SERVER_PORT = env.SERVER_PORT;
const SERVER_HOST = env.SERVER_HOST;

// Create an Express application

const app = express();

app.use(express.json());
app.use(cors());

async function startServer() {
  // Initialize Oracle Database

  if (!(await db.initialize())) {
    console.error('Failed to connect to Oracle Database, Exiting ...')
    return
  }

  // Launch Mosquitto Service

  require('./services/mosquitto')

  // Define a simple route for testing

app.get('/', (req, res) => {
  res.send('Hello, Clinic IoT Backend is running!');
});

  // Import and use routers
  // TODO: Uncomment and implement the routers for routers, devices, and records
  const authRouter = require('./routes/auth');
  const settingsRouter = require('./routes/settings');
  const patientsRouter = require('./routes/patients');
  const routersRouter = require('./routes/routers');
  const devicesRouter = require('./routes/devices');
  const recordsRouter = require('./routes/records');

  app.use('/auth', authRouter);
  app.use('/settings', authMiddleware, settingsRouter);
  app.use('/patients', authMiddleware, patientsRouter);
  app.use('/routers', authMiddleware, routersRouter);
  app.use('/devices', authMiddleware, devicesRouter);
  app.use('/records', authMiddleware, recordsRouter);

  // Start the server

  app.listen(SERVER_PORT, SERVER_HOST, () => {
    console.log(`Server is running on ${SERVER_HOST}:${SERVER_PORT}`);
  });
}

startServer();

// Handle graceful shutdown
process.on("SIGINT", async () => {
  console.log("Shutting down server...");
  await db.closePool();
  process.exit(0);
});