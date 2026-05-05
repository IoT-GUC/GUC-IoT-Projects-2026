const queries = require("../controllers/queries/patients");
const devicesQueries = require("../controllers/queries/devices");
const db = require("../services/oracle-db");
const { arrToBuffer, uuidToBuffer } = require("../controllers/converters/converters");
const uuid = require("uuid");

async function getAllPatients(req, res) {
    try{
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(queries.selectPatients, { hospital_id }, { maxRows: 100 });
        if (result.error) {
            throw result.error;
        }
        res.json({ patients: result.rows })
    } catch (error) {
        res.status(500).json({ error: 'Failed to get patients' })
    }
}

async function getPatientSessions(req, res) {
    try{
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const patient_id = uuidToBuffer(req.params.id);
        // Check if patient exists and belongs to the hospital
        const existsResult = await db.query(queries.selectPatientById, { hospital_id, patient_id });
        if ( existsResult.error || !existsResult.rows.length) {
            return res.status(404).json({ error: 'Patient not found' });
        }
        // Get patient sessions
        const result = await db.query(queries.selectPatientRoutersSessions, { patient_id }, { maxRows: 100 });
        if (result.error) {
            throw result.error;
        }
        res.json({ patient_sessions: result.rows })
    } catch (error) {
        res.status(500).json({ error: 'Failed to get patient sessions' })
    }
}

async function insertPatient(req, res) {
    try{
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const { name, device_id: device_id_str } = req.body;
        const device_id = uuidToBuffer(device_id_str);
        // Check if device exists and belongs to the hospital
        const existsResult = await db.query(devicesQueries.selectDeviceById, { hospital_id, device_id });
        if ( existsResult.error || !existsResult.rows.length) {
            return res.status(404).json({ error: 'Device not found' });
        }
        // Generate new patient ID and insert patient, then update device holder
        const patient_id = uuidToBuffer(uuid.v4());
        const result = await db.query(queries.insertPatient, { hospital_id, patient_id, name }, { autoCommit: true });
        if (result.error) {
            throw result.error;
        }
        const updateDeviceResult = await db.query(devicesQueries.updateDeviceHolder, { patient_id, device_id, hospital_id }, { autoCommit: true });
        if (updateDeviceResult.error) {
            throw updateDeviceResult.error;
        }
        // Return success message
        res.json({ message: 'Patient inserted successfully' })
    } catch (error) {
        res.status(500).json({ error: 'Failed to insert patient' })
    }
}

module.exports = {
    getAllPatients,
    getPatientSessions,
    insertPatient,
}