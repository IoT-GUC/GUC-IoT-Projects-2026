const env = process.env;
const mqtt = require('mqtt');
const recordQueries = require('../controllers/queries/records');
const routerQueries = require('../controllers/queries/routers');
const db = require('../services/oracle-db');
const { isValidMac  } = require('../utils/mac');

// Configuration

const MQTT_BROKER = env.MQTT_BROKER;
const MQTT_PORT = env.MQTT_PORT;
const MQTT_TOPIC = env.MQTT_TOPIC;
const MQTT_ROUTER_TOPIC = env.MQTT_ROUTER_TOPIC;
const MQTT_USERNAME = env.MQTT_USERNAME;
const MQTT_PASSWORD = env.MQTT_PASSWORD;
const DEVICES_SIGNAL_PERIOD = env.DEVICES_SIGNAL_PERIOD;

// Connect to the MQTT broker

const client = mqtt.connect(`${MQTT_BROKER}:${MQTT_PORT}`, {
  username: MQTT_USERNAME,
  password: MQTT_PASSWORD,
});

client.on('connect', () => {
  console.log('Connected to MQTT broker');
  client.subscribe(MQTT_TOPIC, (err) => {
    if (err) {
      console.error('Error subscribing to topic:', err);
    } else {
      console.log('Subscribed to topic:', MQTT_TOPIC);
    }
  });
  client.subscribe(MQTT_ROUTER_TOPIC, (err) => {
    if (err) {
      console.error('Error subscribing to router topic:', err);
    } else {
      console.log('Subscribed to router topic:', MQTT_ROUTER_TOPIC);
    }
  });
});

// Handle incoming MQTT messages

client.on('message', (topic, message) => {
  if (topic === MQTT_TOPIC) onMQTTMessage(topic, message);
  else if (topic === MQTT_ROUTER_TOPIC) onRouterActiveMessage(message);
});


async function onMQTTMessage(topic, message) {
  try {
    const data = JSON.parse(message.toString());
    if (data && isValidMac(data.router_id) && isValidMac(data.device_id) && typeof data.rssi === 'number') {
      const router_id = data.router_id;
      const device_id = data.device_id;
      const rssi = data.rssi;
      const { error, rows } = await db.query(recordQueries.selectRecent2Records, { device_id })
      if (!error)
        if (!rows.length) {
          // The device has no records yet. Insert a new record
          await db.query(recordQueries.insertRecord, { router_id, device_id, rssi }, { autoCommit: true });
        } else {
          // The device has records.
          const timestamp = new Date(rows[0].TIMESTAMP);
          const now = new Date();
          if (now - timestamp < DEVICES_SIGNAL_PERIOD * 1000) {
            // This is a duplicate signal
            if (router_id !== rows[0].ROUTER_ID && rows[0].RSSI < rssi){
              // Assign the record to the the router with the highest RSSI
              await db.query(recordQueries.updateRecord, { router_id, rssi, record_id: rows[0].ID }, { autoCommit: true });
            }
          } else {
            // This is a new signal
            if (rows.length >= 2 && router_id === (rows[0].ROUTER_ID) && router_id === (rows[1].ROUTER_ID)) {
              // The device has at least two consecutive records from the current router.
              await db.query(recordQueries.updateRecord, { router_id, rssi, record_id: rows[0].ID }, { autoCommit: true });
            } else {
              // The device has only one record from the current router.
              await db.query(recordQueries.insertRecord, { router_id, device_id, rssi }, { autoCommit: true });
            }
          }
        }
    }
  } catch (error) {
  }
}

async function onRouterActiveMessage(message) {
  try {
    const data = JSON.parse(message.toString());
    if (data && isValidMac(data.router_id) && data.status === 'active') {
      const router_id = data.router_id;
      await db.query(routerQueries.updateRouterLastActive, { router_id }, { autoCommit: true });
    }
  } catch (error) {
  }
}