const queries = require("../controllers/queries/devices");
const patientQueries = require("../controllers/queries/patients");
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
        const result = await db.query(queries.insertDevice, { hospital_id, device_id, name }, { autoCommit: true });
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
        const device_id = req.params.id;
        const result = await db.query(queries.updateDeviceHolder, { device_id, hospital_id, patient_id: null}, { autoCommit: true });
        if (result.error) {
            throw result.error;
        }
        res.json({ message: 'Device released successfully' })
    }catch (error) {
        res.status(500).json({ error: 'Failed to release device' })
    }
}


async function renameDevice(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const device_id   = req.params.id;
        const { name }    = req.body;
        // Reject if another device in this hospital already has that name
        const conflict = await db.query(queries.selectDeviceByNameExcluding,
            { hospital_id, name, device_id });
        if (conflict.error) throw conflict.error;
        if (conflict.rows.length) {
            return res.status(400).json({ message: "A device with that name already exists" });
        }
        const result = await db.query(queries.updateDeviceName,
            { device_id, hospital_id, name }, { autoCommit: true });
        if (result.error) throw result.error;
        res.json({ message: "Device renamed successfully" });
    } catch (error) {
        res.status(500).json({ error: "Failed to rename device" });
    }
}

async function reassignDevice(req, res) {
    try {
        const hospital_id    = arrToBuffer(req.hospital.id.data);
        const device_id      = req.params.id;
        const { patient_id } = req.body;

        let patient_id_buf = null;
        if (patient_id) {
            patient_id_buf = uuidToBuffer(patient_id);
            // Verify patient belongs to this hospital
            const patientCheck = await db.query(patientQueries.selectPatientById,
                { patient_id: patient_id_buf, hospital_id });
            if (patientCheck.error) throw patientCheck.error;
            if (!patientCheck.rows.length) {
                return res.status(404).json({ error: "Patient not found" });
            }
        }

        const result = await db.query(queries.updateDeviceHolder,
            { device_id, hospital_id, patient_id: patient_id_buf }, { autoCommit: true });
        if (result.error) throw result.error;
        res.json({ message: "Device reassigned successfully" });
    } catch (error) {
        res.status(500).json({ error: "Failed to reassign device" });
    }
}


module.exports = {
    getAllDevices,
    getAllDevicesWithRoutersInfo,
    insertDevice,
    releaseDevice,
    renameDevice,
    reassignDevice,
}