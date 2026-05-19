const bcrypt = require("bcrypt");
const authQueries = require("../controllers/queries/auth");
const patientQueries = require("../controllers/queries/patients");
const routerQueries = require("../controllers/queries/routers");
const deviceQueries = require("../controllers/queries/devices");
const db = require("../services/oracle-db");
const { arrToBuffer } = require("../controllers/converters/converters");
const { uploadImage, getImage, createImagePAR, deleteImage } = require("../services/oracle-obj");


async function getSettings(req, res) {
    try{
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(authQueries.selectHospitalData, { id: hospital_id });
        if (result.error || !result.rows.length) {
            throw result.error || new Error('Hospital not found');
        }
        res.status(200).json({ settings: result.rows[0] });
    } catch (error) {
        res.status(500).json({ error: 'Failed to get settings' });
    }
}

async function updateSettings(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const { name, address, admin_name, admin_email, password } = req.body;
        // Get current hospital settings
        const currentSettingsResult = await db.query(authQueries.selectHospital, { id: hospital_id });
        if (currentSettingsResult.error || !currentSettingsResult.rows.length) {
            throw currentSettingsResult.error || new Error('Hospital not found');
        }
        const currentSettings = currentSettingsResult.rows[0];
        // Encrypt password if provided, otherwise keep current
        let updatedPassword = currentSettings.PASSWORD;
        if (password) {
            updatedPassword = await bcrypt.hash(password, 10);
        }
        // Create update object with new values or keep current values if not provided
        const updateData = {
            id: hospital_id,
            name: name || currentSettings.NAME,
            address: address || currentSettings.ADDRESS,
            admin_name: admin_name || currentSettings.ADMIN_NAME,
            admin_email: admin_email || currentSettings.ADMIN_EMAIL,
            password: updatedPassword,
        };
        // Update hospital settings
        const result = await db.query(authQueries.updateHospital, updateData, { autoCommit: true });
        if (result.error) {
            throw result.error;
        }
        res.status(200).json({ message: "Settings updated successfully" });
    } catch (error) {
        res.status(500).json({ error: 'Failed to update settings' });
    }
}

async function updateBlueprint(req, res) {
    try {
        const file = req.file;

        if (!file) {
            return res.status(400).json({ error: 'No file uploaded' });
        }
        if (file.mimetype !== 'image/jpeg' && file.mimetype !== 'image/png') {
            return res.status(400).json({ error: 'Invalid file type' });
        }
        if (file.size > 5 * 1024 * 1024) {
            return res.status(400).json({ error: 'File size exceeds 5MB' });
        }

        const ref = `${Date.now()}-${file.originalname}`;

        await uploadImage(file.buffer, ref, file.mimetype);

        const hospital_id = arrToBuffer(req.hospital.id.data);

        // Delete old blueprint
        const currentSettings = await db.query(authQueries.selectHospitalBlueprint, { id: hospital_id });
        if (!currentSettings.error && currentSettings.rows.length && currentSettings.rows[0].BLUEPRINT) {
            await deleteImage(currentSettings.rows[0].BLUEPRINT);
        }

        // Update hospital blueprint
        const result = await db.query(authQueries.updateHospitalBlueprint, { id: hospital_id, blueprint: ref }, { autoCommit: true });
        if (result.error) {
            throw result.error;
        }

        res.status(200).json({ message: "Blueprint updated successfully" });
    } catch (err) {
        res.status(500).json({ error: 'Failed to update blueprint' });
    }
}

async function getBlueprint(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(authQueries.selectHospitalBlueprint, { id: hospital_id });
        if (result.error || !result.rows.length || !result.rows[0].BLUEPRINT) {
            throw result.error || new Error('Blueprint not found');
        }

        const ref = result.rows[0].BLUEPRINT;

        const imgUri = await createImagePAR(ref);

        res.status(200).json({ url: imgUri });

    } catch (err) {
        res.status(404).json({ error: "Image not found" });
    }
}

async function resetRecords(req, res) {
    if (req.body?.confirm !== true) {
        return res.status(400).json({ error: 'Must send { "confirm": true } to reset records' });
    }
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(patientQueries.deletePatients, { hospital_id }, { autoCommit: true });
        if (result.error) {
            throw result.error;
        }
        res.status(200).json({ message: "Patients reset successfully" });
    } catch (error) {
        res.status(500).json({ error: 'Failed to reset records' })
    }
}

async function deleteAccount(req, res) {
    try {
        const hospital_id = arrToBuffer(req.hospital.id.data);
        const result = await db.query(routerQueries.deleteRouters, { hospital_id }, { autoCommit: true });
        if (result.error) {
            throw result.error;
        }
        const result2 = await db.query(deviceQueries.deleteDevices, { hospital_id }, { autoCommit: true });
        if (result2.error) {
            throw result2.error;
        }
        const result3 = await db.query(patientQueries.deletePatients, { hospital_id }, { autoCommit: true });
        if (result3.error) {
            throw result3.error;
        }
        const blueprint = await db.query(authQueries.selectHospitalBlueprint, { id: hospital_id });
        if (!blueprint.error && blueprint.rows.length && blueprint.rows[0].BLUEPRINT) {
            await deleteImage(blueprint.rows[0].BLUEPRINT);
        }
        const result4 = await db.query(authQueries.deleteHospital, { id: hospital_id }, { autoCommit: true });
        if (result4.error) {
            throw result4.error;
        }
        res.status(200).json({ message: "Account deleted successfully" });
    } catch (error) {
        res.status(500).json({ error: 'Failed to delete account' })
    }
}

module.exports = {
    getSettings,
    updateSettings,
    updateBlueprint,
    getBlueprint,
    resetRecords,
    deleteAccount
};