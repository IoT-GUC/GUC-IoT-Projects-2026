const selectDevices = `
    SELECT
        id AS "id",
        name AS "name",
        raw_to_uuid(patient_id) AS "patient_id"
    FROM devices
    WHERE hospital_id = :hospital_id
`;

const selectDevicesRouters = `
    SELECT
        id AS "id",
        name AS "name",
        router_id AS "router_id",
        router_name AS "router_name",
        holder_name AS "holder_name",
        last_record_timestamp AS "last_record_timestamp"
    FROM devices_routers
    WHERE hospital_id = :hospital_id
`;

const selectDeviceById = `
    SELECT * FROM devices
    WHERE id = :device_id
    AND hospital_id = :hospital_id
`;

const selectDeviceByName = `
    SELECT * FROM devices
    WHERE name = :name
    AND hospital_id = :hospital_id
`;

const insertDevice = `
    INSERT INTO devices (id, hospital_id, name)
    VALUES (:device_id, :hospital_id, :name)
`;

const updateDeviceHolder = `
    UPDATE devices
    SET patient_id = :patient_id
    WHERE id = :device_id
    AND hospital_id = :hospital_id
`;

const updateDeviceName = `
    UPDATE devices
    SET name = :name
    WHERE id = :device_id
    AND hospital_id = :hospital_id
`;

// Name uniqueness check that excludes the device being renamed
const selectDeviceByNameExcluding = `
    SELECT id FROM devices
    WHERE name = :name
    AND hospital_id = :hospital_id
    AND id != :device_id
`;

const deleteDevices = `
    DELETE FROM devices
    WHERE hospital_id = :hospital_id
`;


module.exports = {
    selectDevices,
    selectDevicesRouters,
    selectDeviceById,
    selectDeviceByName,
    selectDeviceByNameExcluding,
    insertDevice,
    updateDeviceHolder,
    updateDeviceName,
    deleteDevices
};