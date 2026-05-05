const queries = require("../controllers/queries/devices");
const db = require("../services/oracle-db");
const { arrToBuffer, uuidToBuffer } = require("../controllers/converters/converters");

async function getAllDevices(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(queries.selectDevices, { hospital_id }, { maxRows: 100 });
        if (result.error) {
            throw result.error;
        }
        res.json({ devices: result.rows })
    } catch (error) {
        res.status(500).json({ error: 'Failed to get devices' })
    }
}

async function getAllDevicesWithRoutersInfo(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(queries.selectDevicesRouters, { hospital_id }, { maxRows: 100 });
        if (result.error) {
            throw result.error;
        }
        res.json({ devices: result.rows })
    } catch (error) {
        res.status(500).json({ error: 'Failed to get devices' })
    }
}

async function insertDevice(req, res) {
    try{
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const { device_id, name } = req.body;
        // Check if device already exists
        const existsResult = await db.query(queries.selectDeviceByName, { hospital_id, name });
        if ( existsResult.error || existsResult.rows.length) {
            return res.status(400).json({ error: 'Device name already exists' });
        }
        // Insert device
        const result = await db.query(queries.insertDevice, { hospital_id, device_id: uuidToBuffer(device_id), name }, { autoCommit: true });
        if (result.error) {
            throw result.error;
        }
        res.json({ message: 'Device inserted successfully' })
    } catch (error) {
        res.status(500).json({ error: 'Failed to insert device' })
    }
}

async function releaseDevice(req, res) {
    try{
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const device_id = uuidToBuffer(req.params.id);
        const result = await db.query(queries.updateDeviceHolder, { device_id, hospital_id, patient_id: null}, { autoCommit: true });
        if (result.error) {
            throw result.error;
        }
        res.json({ message: 'Device released successfully' })
    }catch (error) {
        res.status(500).json({ error: 'Failed to release device' })
    }
}


module.exports = {
    getAllDevices,
    getAllDevicesWithRoutersInfo,
    insertDevice,
    releaseDevice,
}