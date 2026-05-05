const selectPatients = `
    SELECT
        raw_to_uuid(id) AS "id",
        name AS "name"
    FROM patients WHERE hospital_id = :hospital_id
`;

const selectPatientById = `
    SELECT * FROM patients
    WHERE id = :patient_id
    AND hospital_id = :hospital_id
`;


const selectPatientRoutersSessions = `
    SELECT
        raw_to_uuid(patient_id) AS "patient_id",
        raw_to_uuid(router_id) AS "router_id",
        routers.name AS "router_name",
        start_time AS "start_time",
        duration_seconds AS "duration"
    FROM patients_routers_sessions
    JOIN routers ON patients_routers_sessions.router_id = routers.id
    WHERE patient_id = :patient_id
    ORDER BY start_time ASC
`;

const insertPatient = `
    INSERT INTO patients (id, hospital_id, name)
    VALUES (:patient_id, :hospital_id, :name)
`;

const deletePatients = `
    DELETE FROM patients
    WHERE hospital_id = :hospital_id
`;


module.exports = {
    selectPatients,
    selectPatientById,
    selectPatientRoutersSessions,
    insertPatient,
    deletePatients
};