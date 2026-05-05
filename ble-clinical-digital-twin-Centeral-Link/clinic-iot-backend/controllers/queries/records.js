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


module.exports = {
    selectHourlyRecords,
    selectHourlyPatients,
    selectPatientsHourlySessions,
    selectRecent2Records,
    insertRecord,
    updateRecord
};