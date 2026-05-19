const selectHourlyRecords = `
    SELECT
        hour AS "hour",
        records_count AS "records_count"
    FROM hourly_records
    WHERE hospital_id = :hospital_id
`;

const selectHourlyPatients = `
    SELECT
        hour AS "hour",
        patients_count AS "patients_count"
    FROM hourly_patients
    WHERE hospital_id = :hospital_id
`;

const selectPatientsHourlySessions = `
    SELECT
        TRUNC (earliest_start_time, 'HH') AS "hour",
        AVG (total_duration) AS "average_total_session_duration"
    FROM patients_sessions
    JOIN patients ON patients_sessions.patient_id = patients.id
    WHERE hospital_id = :hospital_id
    GROUP BY TRUNC (earliest_start_time, 'HH')
    ORDER BY TRUNC (earliest_start_time, 'HH')
`;

const selectRecent2Records = `
    SELECT records.*
    FROM records
    JOIN devices ON records.patient_id = devices.patient_id
    WHERE devices.id = :device_id
    ORDER BY records.timestamp DESC
    FETCH FIRST 2 ROWS ONLY
`;


const insertRecord = `
    INSERT INTO records (router_id, patient_id, rssi)
    SELECT :router_id, patient_id, :rssi
    FROM devices
    WHERE devices.id = :device_id
`;

const updateRecord = `
    UPDATE records
    SET router_id = :router_id,
        rssi = :rssi,
        timestamp = CURRENT_TIMESTAMP
    WHERE id = :record_id
`;


// Per-room: unique patients per hour of day (0–23), across all days
const selectRoomsHourlyOccupancy = `
    SELECT
        rec.router_id AS "router_id",
        r.name                     AS "router_name",
        EXTRACT(HOUR FROM rec.timestamp) AS "hour_of_day",
        COUNT(DISTINCT rec.patient_id)   AS "patient_count"
    FROM records rec
    JOIN routers r ON rec.router_id = r.id
    WHERE r.hospital_id = :hospital_id
    GROUP BY rec.router_id, r.name, EXTRACT(HOUR FROM rec.timestamp)
    ORDER BY rec.router_id, EXTRACT(HOUR FROM rec.timestamp)
`;

// Per-room: avg dwell time + total sessions, ranked by highest avg dwell
const selectRoomsDwellTime = `
    SELECT
        prs.router_id        AS "router_id",
        r.name                            AS "router_name",
        COUNT(*)                          AS "total_sessions",
        ROUND(AVG(prs.duration_seconds))  AS "avg_dwell_seconds",
        ROUND(SUM(prs.duration_seconds))  AS "total_dwell_seconds"
    FROM patients_routers_sessions prs
    JOIN routers r ON prs.router_id = r.id
    WHERE r.hospital_id = :hospital_id
    GROUP BY prs.router_id, r.name
    ORDER BY AVG(prs.duration_seconds) DESC
`;

// Per-patient per-room: how long each patient spent in each room
const selectPatientsRoomStats = `
    SELECT
        raw_to_uuid(prs.patient_id)       AS "patient_id",
        p.name                            AS "patient_name",
        prs.router_id                     AS "router_id",
        r.name                            AS "router_name",
        COUNT(*)                          AS "visit_count",
        ROUND(SUM(prs.duration_seconds))  AS "total_seconds",
        ROUND(AVG(prs.duration_seconds))  AS "avg_seconds"
    FROM patients_routers_sessions prs
    JOIN patients p ON prs.patient_id = p.id
    JOIN routers  r ON prs.router_id  = r.id
    WHERE p.hospital_id = :hospital_id
    GROUP BY prs.patient_id, p.name, prs.router_id, r.name
    ORDER BY prs.patient_id, SUM(prs.duration_seconds) DESC
`;

// Average total visit duration across all patients (today)
const selectAvgVisitTime = `
    SELECT
        ROUND(AVG(total_duration)) AS "avg_visit_seconds",
        COUNT(*)                   AS "patient_count"
    FROM patients_sessions
    JOIN patients ON patients_sessions.patient_id = patients.id
    WHERE patients.hospital_id = :hospital_id
      AND TRUNC(earliest_start_time) = TRUNC(SYSDATE)
`;

module.exports = {
    selectHourlyRecords,
    selectHourlyPatients,
    selectPatientsHourlySessions,
    selectRecent2Records,
    insertRecord,
    updateRecord,
    selectRoomsHourlyOccupancy,
    selectRoomsDwellTime,
    selectPatientsRoomStats,
    selectAvgVisitTime,
};