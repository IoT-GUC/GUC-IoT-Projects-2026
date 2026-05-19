const env = process.env;
const queries = require("../controllers/queries/routers");
const db = require("../services/oracle-db");
const { arrToBuffer, uuidToBuffer, bufferToUuid } = require("../controllers/converters/converters");

const ROUTER_ACTIVE_INTERVAL = Number(env.ROUTER_ACTIVE_INTERVAL);

async function getAllRouters(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(queries.selectRouters, { hospital_id });
        if (result.error) {
            throw result.error;
        }
        res.json({ routers: result.rows })
    } catch (error) {
        res.status(500).json({ error: 'Failed to get routers' })
    }
}

async function getRoutersMap(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(queries.selectRoutersMap, { hospital_id });
        if (result.error) {
            throw result.error;
        }
        res.json({ routers_map: result.rows })
    } catch (error) {
        res.status(500).json({ error: 'Failed to get routers map' })
    }
}

async function getRouterById(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const router_id = req.params.id;
        const result = await db.query(queries.selectRouterById, { router_id, hospital_id });
        if (result.error) {
            throw result.error;
        }
        const router = result.rows[0];
        res.json({
            router: {
                id: bufferToUuid(router.ID),
                name: router.NAME,
                location_x: router.LOCATION_X,
                location_y: router.LOCATION_Y
            }
        })
    } catch (error) {
        res.status(500).json({ error: 'Failed to get router' })
    }
}

async function getRouterConnectedDevices(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const router_id = req.params.id;
        const result = await db.query(queries.selectRouterConnectedDevices, { router_id, hospital_id }, { maxRows: 100 });
        if (result.error) {
            throw result.error;
        }
        res.json({ devices: result.rows })
    } catch (error) {
        res.status(500).json({ error: 'Failed to get router connected devices' })
    }
}

async function getRouterHourlySessionsDuration(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const router_id = req.params.id;
        // Check if router exists and belongs to the hospital
        const existsResult = await db.query(queries.selectRouterById, { router_id, hospital_id });
        if (existsResult.error || !existsResult.rows.length) {
            return res.status(404).json({ error: 'Router not found' });
        }
        // Get router hourly sessions duration
        const result = await db.query(queries.selectRoutersHourlySessions, { router_id }, { maxRows: 100 });
        if (result.error) {
            throw result.error;
        }
        res.json({ hourly_sessions: result.rows })
    } catch (error) {
        console.error('Get router hourly sessions error: ', error)
        res.status(500).json({ error: 'Failed to get router hourly sessions' })
    }
}

async function getActiveRouters(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(queries.selectActiveRouters, { hospital_id, active_interval: ROUTER_ACTIVE_INTERVAL });
        if (result.error) {
            throw result.error;
        }
        res.json({ routers: result.rows });
    } catch (error) {
        res.status(500).json({ error: 'Failed to get active routers' });
    }
}

async function insertRouter(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const { router_id, name, location_x, location_y } = req.body;
        // Check if router already exists
        const existsResult = await db.query(queries.selectRouterByName, { name, hospital_id });
        if (existsResult.error || existsResult.rows.length) {
            return res.status(400).json({ error: 'Router name already exists' });
        }
        // Insert router
        const result = await db.query(queries.insertRouter, { hospital_id, router_id, name, location_x, location_y }, { autoCommit: true });
        if (result.error) {
            throw result.error;
        }
        res.json({ message: 'Router inserted successfully' })
    } catch (error) {
        res.status(500).json({ error: 'Failed to insert router' })
    }
}

module.exports = {
    getAllRouters,
    getRoutersMap,
    getActiveRouters,
    getRouterById,
    getRouterConnectedDevices,
    getRouterHourlySessionsDuration,
    insertRouter,
}