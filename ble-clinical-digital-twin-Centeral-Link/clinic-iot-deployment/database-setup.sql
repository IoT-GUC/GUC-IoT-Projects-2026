-- OracleDB SQL script to set up the database schema for routers, devices, and their connection records
-- Create Table hospitals
CREATE TABLE hospitals (
    id RAW (16) DEFAULT SYS_GUID () PRIMARY KEY,
    hospital_id VARCHAR2 (255) UNIQUE NOT NULL,
    name VARCHAR2 (255) NOT NULL,
    address VARCHAR2 (255),
    admin_name VARCHAR2 (255),
    admin_email VARCHAR2 (255),
    password VARCHAR2 (255) NOT NULL,
    blueprint VARCHAR2 (255)
);

CREATE TABLE patients (
    id RAW (16) DEFAULT SYS_GUID () PRIMARY KEY,
    hospital_id RAW (16),
    name VARCHAR2 (255) NOT NULL,
    CONSTRAINT fk_pat_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals (id)
);

CREATE TABLE routers (
    id RAW (16) DEFAULT SYS_GUID () PRIMARY KEY,
    hospital_id RAW (16),
    name VARCHAR2 (255) NOT NULL,
    location_x NUMBER DEFAULT 0,
    location_y NUMBER DEFAULT 0,
    CONSTRAINT fk_router_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals (id),
    CONSTRAINT uq_router UNIQUE (hospital_id, name)
);

CREATE TABLE devices (
    id RAW (16) DEFAULT SYS_GUID () PRIMARY KEY,
    hospital_id RAW (16),
    patient_id RAW (16),
    name VARCHAR2 (255) NOT NULL,
    CONSTRAINT fk_dev_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals (id),
    CONSTRAINT fk_dev_patient FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE SET NULL,
    CONSTRAINT uq_device UNIQUE (hospital_id, name)
);

CREATE TABLE records (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    router_id RAW (16),
    patient_id RAW (16),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    rssi NUMBER NOT NULL,
    CONSTRAINT fk_rec_router FOREIGN KEY (router_id) REFERENCES routers (id) ON DELETE CASCADE,
    CONSTRAINT fk_rec_patient FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
);

-- Create index
CREATE INDEX routers_hid_idx ON routers (hospital_id);

CREATE INDEX devices_hid_idx ON devices (hospital_id);

CREATE INDEX patients_hid_idx ON patients (hospital_id);

CREATE INDEX records_rid_idx ON records(router_id);

CREATE INDEX records_pid_idx ON records(patient_id);

CREATE INDEX devices_pid_idx ON devices(patient_id);

-- Create latest_records that returns the latest record for each device
CREATE OR REPLACE VIEW latest_records AS
SELECT
    d.id AS device_id,
    r.router_id,
    r.timestamp
FROM devices d
CROSS APPLY (
    SELECT r.router_id, r.timestamp
    FROM records r
    WHERE r.patient_id = d.patient_id
    ORDER BY r.timestamp DESC
    FETCH FIRST 1 ROW ONLY
) r;

-- Create routers_map that returns a map of all routers with their locations and the count of connected devices
CREATE
OR REPLACE VIEW routers_map AS
SELECT
    routers.id,
    routers.hospital_id,
    routers.location_x,
    routers.location_y,
    COUNT(latest_records.device_id) AS connected_devices_count
FROM
    routers
    LEFT JOIN latest_records ON routers.id = latest_records.router_id
GROUP BY
    routers.id,
    routers.hospital_id,
    routers.location_x,
    routers.location_y;

-- Create devices_routers that returns a map of all devices with their connections
CREATE
OR REPLACE VIEW devices_routers AS
SELECT
    devices.id,
    devices.hospital_id,
    devices.name,
    patients.name AS holder_name,
    latest_records.timestamp AS last_record_timestamp,
    routers.id AS router_id,
    routers.name AS router_name
FROM
    devices
    JOIN patients ON devices.patient_id = patients.id
    JOIN latest_records ON devices.id = latest_records.device_id
    JOIN routers ON routers.id = latest_records.router_id;

-- Create hourly_records that returns the number of records created each hour
CREATE
OR REPLACE VIEW hourly_records AS
SELECT
    routers.hospital_id,
    TRUNC (records.timestamp, 'HH') AS hour,
    COUNT(*) AS records_count
FROM
    records
    JOIN routers ON records.router_id = routers.id
GROUP BY
    routers.hospital_id,
    TRUNC (records.timestamp, 'HH')
ORDER BY
    routers.hospital_id,
    TRUNC (records.timestamp, 'HH');

-- Create hourly_patients that returns the number of patients seen each hour
CREATE
OR REPLACE VIEW hourly_patients AS
SELECT
    routers.hospital_id,
    TRUNC (records.timestamp, 'HH') AS hour,
    COUNT(DISTINCT records.patient_id) AS patients_count
FROM
    records
    JOIN routers ON records.router_id = routers.id
GROUP BY
    routers.hospital_id,
    TRUNC (records.timestamp, 'HH')
ORDER BY
    routers.hospital_id,
    TRUNC (records.timestamp, 'HH');

-- Create patients_routers_sessions that returns the total session duration for each patient
CREATE
OR REPLACE VIEW patients_routers_sessions AS
SELECT mr_patient_id AS patient_id,
       mr_router_id  AS router_id,
       start_time,
       duration_seconds
FROM records
MATCH_RECOGNIZE (
    PARTITION BY patient_id
    ORDER BY timestamp
    MEASURES
        FIRST(patient_id) AS mr_patient_id,
        FIRST(router_id)  AS mr_router_id,
        FIRST(timestamp)  AS start_time,
        (CAST(LAST(timestamp) AS DATE) - CAST(FIRST(timestamp) AS DATE)) * 86400
            AS duration_seconds
    ONE ROW PER MATCH
    PATTERN (A{2,})
    DEFINE
        A AS router_id = FIRST(router_id)
)
ORDER BY patient_id, start_time;


-- Create routers_hourly_sessions that returns the number of connected devices and the average session duration
CREATE
OR REPLACE VIEW routers_hourly_sessions AS
SELECT
    router_id,
    TRUNC (start_time, 'HH') AS hour,
    COUNT(*) AS sessions_count,
    AVG(duration_seconds) AS average_session_duration
FROM
    patients_routers_sessions
GROUP BY
    router_id,
    TRUNC (start_time, 'HH');

-- Create patients_sessions that returns the earliest start time and total session duration for each patient
CREATE
OR REPLACE VIEW patients_sessions AS
SELECT
    patient_id,
    MIN(start_time) AS earliest_start_time,
    SUM(duration_seconds) AS total_duration
FROM
    patients_routers_sessions
GROUP BY
    patient_id;

-- Create patients_hourly_sessions that returns the average session duration for each patient
CREATE
OR REPLACE VIEW patients_hourly_sessions AS
SELECT
    TRUNC (earliest_start_time, 'HH') AS hour,
    AVG(total_duration) AS average_total_session_duration
FROM
    patients_sessions
GROUP BY
    TRUNC (patients_sessions.earliest_start_time, 'HH');


CREATE OR REPLACE FUNCTION raw_to_uuid(p_raw IN RAW)
RETURN VARCHAR2
DETERMINISTIC
IS
    h VARCHAR2(32);
BEGIN
    IF p_raw IS NULL THEN
        RETURN NULL;
    END IF;

    h := LOWER(RAWTOHEX(p_raw));

    RETURN SUBSTR(h, 1, 8)  || '-' ||
           SUBSTR(h, 9, 4)  || '-' ||
           SUBSTR(h, 13, 4) || '-' ||
           SUBSTR(h, 17, 4) || '-' ||
           SUBSTR(h, 21, 12);
END;

--
--
--
--
-- Using Materealized Views
CREATE TABLE records (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    router_id RAW (16),
    patient_id RAW (16),
    device_id RAW (16),
    timestamp TIMESTAMP DEFAULT SYSTIMESTAMP,
    rssi NUMBER NOT NULL
)
PARTITION BY
    RANGE (timestamp) INTERVAL(NUMTODSINTERVAL (1, 'DAY')) (
        PARTITION p0
        VALUES
            LESS THAN (TIMESTAMP '2026-01-01 00:00:00')
    );

CREATE INDEX idx_records_router_time ON records (router_id, timestamp);

CREATE INDEX idx_records_patient_time ON records (patient_id, timestamp);

CREATE INDEX idx_records_device_time ON records (device_id, timestamp);

CREATE MATERIALIZED VIEW latest_records_mv BUILD IMMEDIATE REFRESH FAST ON COMMIT AS
SELECT
    device_id,
    router_id,
    timestamp
FROM
    (
        SELECT
            device_id,
            router_id,
            timestamp,
            ROW_NUMBER() OVER (
                PARTITION BY
                    device_id
                ORDER BY
                    timestamp DESC
            ) rn
        FROM
            records
    )
WHERE
    rn = 1;

CREATE MATERIALIZED VIEW routers_map_mv BUILD IMMEDIATE REFRESH FAST ON COMMIT AS
SELECT
    r.id,
    r.hospital_id,
    r.location_x,
    r.location_y,
    COUNT(l.device_id) AS connected_devices_count
FROM
    routers r
    LEFT JOIN latest_records_mv l ON r.id = l.router_id
GROUP BY
    r.id,
    r.hospital_id,
    r.location_x,
    r.location_y;

CREATE MATERIALIZED VIEW hourly_records_mv BUILD IMMEDIATE REFRESH FAST ON COMMIT AS
SELECT
    routers.hospital_id,
    TRUNC (records.timestamp, 'HH') AS hour,
    COUNT(*) AS records_count
FROM
    records
    JOIN routers ON records.router_id = routers.id
GROUP BY
    routers.hospital_id,
    TRUNC (records.timestamp, 'HH');

CREATE MATERIALIZED VIEW patient_router_sessions_mv BUILD IMMEDIATE REFRESH FAST ON COMMIT AS
SELECT
    patient_id,
    router_id,
    MIN(timestamp) AS start_time,
    (
        CAST(MAX(timestamp) AS DATE) - CAST(MIN(timestamp) AS DATE)
    ) * 86400 AS duration_seconds
FROM
    records
GROUP BY
    patient_id,
    router_id;

CREATE MATERIALIZED VIEW router_hourly_sessions_mv BUILD IMMEDIATE REFRESH FAST ON COMMIT AS
SELECT
    router_id,
    TRUNC (start_time, 'HH') AS hour,
    COUNT(*) AS sessions_count,
    AVG(duration_seconds) AS avg_session_duration
FROM
    patient_router_sessions_mv
GROUP BY
    router_id,
    TRUNC (start_time, 'HH');