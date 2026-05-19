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

async function getRoomsHourlyOccupancy(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(queries.selectRoomsHourlyOccupancy, { hospital_id }, { maxRows: 2400 });
        if (result.error) throw result.error;
        res.json({ rooms_hourly_occupancy: result.rows });
    } catch (error) {
        res.status(500).json({ error: 'Failed to get rooms hourly occupancy' });
    }
}

async function getRoomsDwellTime(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(queries.selectRoomsDwellTime, { hospital_id }, { maxRows: 100 });
        if (result.error) throw result.error;
        res.json({ rooms_dwell_time: result.rows });
    } catch (error) {
        res.status(500).json({ error: 'Failed to get rooms dwell time' });
    }
}

async function getPatientsRoomStats(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(queries.selectPatientsRoomStats, { hospital_id }, { maxRows: 1000 });
        if (result.error) throw result.error;
        res.json({ patients_room_stats: result.rows });
    } catch (error) {
        res.status(500).json({ error: 'Failed to get patients room stats' });
    }
}

async function getAvgVisitTime(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(queries.selectAvgVisitTime, { hospital_id });
        if (result.error) throw result.error;
        const row = result.rows[0] || {};
        res.json({
            avg_visit_seconds: row.avg_visit_seconds || 0,
            patient_count:     row.patient_count     || 0,
        });
    } catch (error) {
        res.status(500).json({ error: 'Failed to get avg visit time' });
    }
}

module.exports = {
    getHourlyRecordsCount,
    getHourlyPatientsCount,
    getRouterHourlyTotalSessionsDuration,
    getRoomsHourlyOccupancy,
    getRoomsDwellTime,
    getPatientsRoomStats,
    getAvgVisitTime,
}