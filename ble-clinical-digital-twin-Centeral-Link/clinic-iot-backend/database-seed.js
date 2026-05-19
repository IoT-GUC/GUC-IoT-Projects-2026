/*
* Database seeding script for populating the database with initial data.
* This script can be run using Node.js to insert sample data into the database.
* Usage: node database-seed.js
*/
require('dotenv').config();
const bcrypt = require("bcrypt");
const uuid = require("uuid");
const oracledb = require("oracledb");
const authQueries = require("./controllers/queries/auth");
const patientQueries = require("./controllers/queries/patients");
const routerQueries = require("./controllers/queries/routers");
const deviceQueries = require("./controllers/queries/devices");
const db = require("./services/oracle-db");
const { arrToBuffer, uuidToBuffer } = require("./controllers/converters/converters");
const { generateMac } = require("./utils/mac");

async function clearDatabase() {
    console.log('Clearing database...');
    const { error } = await db.query('DELETE FROM RECORDS', [], { autoCommit: true });
    if (error) {
        console.error('Error clearing existing records:', error);
        process.exit(1);
    }
    const { error: deviceError } = await db.query('DELETE FROM DEVICES', [], { autoCommit: true });
    if (deviceError) {
        console.error('Error clearing existing devices:', deviceError);
        process.exit(1);
    }
    const { error: patientError } = await db.query('DELETE FROM PATIENTS', [], { autoCommit: true });
    if (patientError) {
        console.error('Error clearing existing patients:', patientError);
        process.exit(1);
    }
    const { error: routerError } = await db.query('DELETE FROM ROUTERS', [], { autoCommit: true });
    if (routerError) {
        console.error('Error clearing existing routers:', routerError);
        process.exit(1);
    }
    const { error: hospitalError } = await db.query('DELETE FROM HOSPITALS', [], { autoCommit: true });
    if (hospitalError) {
        console.error('Error clearing existing hospitals:', hospitalError);
        process.exit(1);
    }
    console.log('Database cleared successfully.');
}

async function seedHospital() {
    console.log('Seeding a hospital...');
    const hospitalData = {
        hospital_id: 'HOSPITAL-SEED',
        name: 'Seed Hospital',
        address: 'Seed Address',
        admin_name: 'Seed Admin',
        admin_email: 'Gx2t2@example.com',
        password: await bcrypt.hash('seedpassword', 10),
        id: { type: oracledb.DB_TYPE_RAW, dir: oracledb.BIND_OUT },
    };
    // Clear existing hospital with the same hospital_id
    const { error } = await db.query('DELETE FROM HOSPITALS', [], { autoCommit: true });
    if (error) {
        console.error('Error clearing existing hospital:', error);
        process.exit(1);
    }
    const { outBinds, error: seedError} = await db.query(authQueries.insertHospital, hospitalData, { autoCommit: true });
    if (!seedError) {
        console.log('Hospital seeded successfully: ', outBinds.id[0]);
        return outBinds.id[0];
    } else {
        console.error('Error seeding hospital:', seedError);
        process.exit(1);
    }
}

async function seedRouters(hospital_id) {
    console.log(hospital_id);
    console.log('Seeding routers...');
    // Clear existing data
    const { error } = await db.query('DELETE FROM ROUTERS', [], { autoCommit: true });
    if (error) {
        console.error('Error clearing existing routers:', error);
        process.exit(1);
    }
    // Seed new data
    const nRouters = 3;
    const routersIds = [];
    for (let i = 0; i < nRouters; i++) {
        const routerData = {
            router_id: generateMac(),
            hospital_id,
            name: `Seed Router ${i + 1}`,
            location_x: Math.random(),
            location_y: Math.random(),
        };
        const { error: seedError} = await db.query(routerQueries.insertRouter, routerData, { autoCommit: true });
        if (!seedError) {
            routersIds.push(routerData.router_id);
        }
    }
    console.log('Routers seeded successfully: ', routersIds.length);
    return routersIds;
}

async function seedPatients(hospital_id) {
    console.log('Seeding patients...');
    // Clear existing data
    const { error } = await db.query('DELETE FROM PATIENTS', [], { autoCommit: true });
    if (error) {
        console.error('Error clearing existing patients:', error);
        process.exit(1);
    }
    // Seed new data
    const nPatients = 10;
    const patientIds = [];
    for (let i = 0; i < nPatients; i++) {
        const patientData = {
            patient_id: uuidToBuffer(uuid.v4()),
            hospital_id,
            name: `Seed Patient ${i + 1}`,
        };
        const { error: seedError } = await db.query(patientQueries.insertPatient, patientData, { autoCommit: true });
        if (!seedError) {
            patientIds.push(patientData.patient_id);
        }
    }
    console.log('Patients seeded successfully: ', patientIds.length);
    return patientIds;
}

async function seedDevices(hospital_id, patient_ids) {
    console.log('Seeding devices...');
    // Clear existing data
    const { error } = await db.query('DELETE FROM DEVICES', [], { autoCommit: true });
    if (error) {
        console.error('Error clearing existing devices:', error);
        process.exit(1);
    }
    // Seed new data
    const devicesIds = [];
    for (let i = 0; i < patient_ids.length; i++) {
        const deviceData = {
            device_id: generateMac(),
            hospital_id,
            name: `Seed Device ${i + 1}`,
        };
        const { error: seedError } = await db.query(deviceQueries.insertDevice, deviceData, { autoCommit: true });
        if (!seedError) {
            devicesIds.push(deviceData.device_id);
        }
        const { error: updateError } = await db.query(deviceQueries.updateDeviceHolder, {
            patient_id: patient_ids[i],
            device_id: deviceData.device_id,
            hospital_id,
        }, { autoCommit: true });
        if (updateError) {
            console.error('Error assigning device to patient:', updateError);
        }
    }
    console.log('Devices seeded successfully: ', devicesIds.length);
    return devicesIds;
}

async function seedDeviceRecords(routersIds, patientId) {
    console.log(`Seeding records for device ${patientId}...`);
    const nRecordsPerRouter = 3;
    const timestamp = new Date();
    timestamp.setHours(Math.floor(Math.random() * 24), Math.floor(Math.random() * 60), 0, 0);
    for (const routerId of routersIds) {
        for (let i = 0; i < nRecordsPerRouter; i++) {
            const recordData = {
                router_id: routerId,
                patient_id: patientId,
                timestamp: timestamp,
                rssi: Math.floor(Math.random() * 100) - 100,
            };
            const { error } = await db.query(`INSERT INTO RECORDS (router_id, patient_id, timestamp, rssi)
                VALUES (:router_id, :patient_id, :timestamp, :rssi)`, recordData, { autoCommit: true });
            if (error) {
                console.error(`Error seeding record for device ${patientId} and router ${routerId}:`, error);
            } else {
                console.log(`Record seeded successfully for device ${patientId} and router ${routerId}`);
            }
            timestamp.setMinutes(timestamp.getMinutes() + Math.ceil(Math.random() * 30));
        }
    }
}

async function seedRecords(routersIds, patientIds) {
    console.log('Seeding records...');
    // Clear existing data
    const { error } = await db.query('DELETE FROM RECORDS', [], { autoCommit: true });
    if (error) {
        console.error('Error clearing existing records:', error);
        process.exit(1);
    }
    // Seed new data
    for (const patientId of patientIds) {
        await seedDeviceRecords(routersIds, patientId);
    }
    console.log('Records seeded successfully.');
}

async function seedDatabase() {
    try {
        console.log('Connecting to database...');
        await db.initialize();
        console.log('Database connected successfully.');
        await clearDatabase();
        console.log('Starting database seeding...');
        const hospital_id = await seedHospital();
        const routersIds = await seedRouters(hospital_id);
        const patientIds = await seedPatients(hospital_id);
        await seedDevices(hospital_id, patientIds);
        await seedRecords(routersIds, patientIds);
        console.log('Database seeded successfully.');
    } catch (error) {
        console.error('Error seeding database:', error);
    } finally {
        await db.closePool();
        process.exit(0);
    }
}

seedDatabase();
