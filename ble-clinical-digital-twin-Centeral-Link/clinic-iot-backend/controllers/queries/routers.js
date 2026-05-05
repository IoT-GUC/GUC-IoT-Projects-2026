const selectRouters = `
    SELECT
        raw_to_uuid(id) AS "id",
        name as "name",
        location_x as "location_x",
        location_y as "location_y"
    FROM routers
    WHERE hospital_id = :hospital_id
`;

const selectRoutersMap = `
    SELECT
        raw_to_uuid(id) AS "id",
        location_x as "location_x",
        location_y as "location_y",
        connected_devices_count as "connected_devices_count"
    FROM routers_map
    WHERE hospital_id = :hospital_id
`;

const selectRoutersHourlySessions = `
    SELECT
        raw_to_uuid(router_id) AS "router_id",
        hour AS "hour",
        sessions_count AS "sessions_count",
        average_session_duration AS "average_session_duration"
    FROM routers_hourly_sessions
    WHERE routers_hourly_sessions.router_id = :router_id
`;

const selectRouterById = `
    SELECT * FROM routers
    WHERE id = :router_id
    AND hospital_id = :hospital_id
`;

const selectRouterByName = `
    SELECT * FROM routers
    WHERE name = :name
    AND hospital_id = :hospital_id
`;

const selectRouterConnectedDevices = `
    SELECT
        raw_to_uuid(id) AS "id",
        name AS "name",
        raw_to_uuid(router_id) AS "router_id",
        router_name AS "router_name",
        holder_name AS "holder_name",
        last_record_timestamp AS "last_record_timestamp"
    FROM devices_routers
    WHERE hospital_id = :hospital_id
    AND router_id = :router_id
`;


const insertRouter = `
    INSERT INTO routers (id, hospital_id, name, location_x, location_y)
    VALUES (:router_id, :hospital_id, :name, :location_x, :location_y)
`;

const deleteRouters = `
    DELETE FROM routers
    WHERE hospital_id = :hospital_id
`;


module.exports = {
    selectRouters,
    selectRoutersMap,
    selectRoutersHourlySessions,
    selectRouterById,
    selectRouterByName,
    selectRouterConnectedDevices,
    insertRouter,
    deleteRouters
};