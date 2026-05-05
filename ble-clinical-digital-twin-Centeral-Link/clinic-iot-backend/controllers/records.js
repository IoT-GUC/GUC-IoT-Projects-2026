const queries = require("../controllers/queries/records");
const db = require("../services/oracle-db");
const { arrToBuffer } = require("../controllers/converters/converters");

async function getHourlyRecordsCount(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(queries.selectHourlyRecords, { hospital_id }, { maxRows: 100 });
        if (result.error) {
            throw result.error;
        }
        res.json({ records_hourly: result.rows })
    } catch (error) {
        res.status(500).json({ error: 'Failed to get hourly records' })
    }
}

async function getHourlyPatientsCount(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(queries.selectHourlyPatients, { hospital_id }, { maxRows: 100 });
        if (result.error) {
            throw result.error;
        }
        res.json({ records_hourly: result.rows })
    } catch (error) {
        res.status(500).json({ error: 'Failed to get hourly patients' })
    }
}

async function getRouterHourlyTotalSessionsDuration(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(queries.selectPatientsHourlySessions, { hospital_id }, { maxRows: 100 });
        if (result.error) {
            throw result.error;
        }
        res.json({ hourly_sessions: result.rows })
    } catch (error) {
        res.status(500).json({ error: 'Failed to get router hourly total sessions duration' })
    }
}

module.exports = {
    getHourlyRecordsCount,
    getHourlyPatientsCount,
    getRouterHourlyTotalSessionsDuration,
}