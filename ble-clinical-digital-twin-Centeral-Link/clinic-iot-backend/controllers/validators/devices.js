const { isValidMac } = require('../../utils/mac');

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function validateDevice(req, res, next) {
    const { device_id, name } = req.body;
    if (!device_id || !name || typeof name !== "string" || name.trim() === "") {
        return res.status(400).json({ message: "Invalid device name" });
    }
    if (!isValidMac(device_id)) {
        return res.status(400).json({ message: "Invalid device ID" });
    }
    if (name.trim().length < 2 || name.length > 100) {
        return res.status(400).json({ message: "Device name must be between 2 and 100 characters" });
    }
    next();
};

function validateRename(req, res, next) {
    const { name } = req.body;
    if (!name || typeof name !== "string" || name.trim() === "") {
        return res.status(400).json({ message: "Name is required" });
    }
    if (name.trim().length < 2 || name.trim().length > 100) {
        return res.status(400).json({ message: "Device name must be between 2 and 100 characters" });
    }
    req.body.name = name.trim();
    next();
}

function validateReassign(req, res, next) {
    const { patient_id } = req.body;
    if (patient_id !== null && patient_id !== undefined) {
        if (typeof patient_id !== "string" || !UUID_RE.test(patient_id)) {
            return res.status(400).json({ message: "patient_id must be a valid UUID or null" });
        }
    }
    next();
}

module.exports = {
    validateDevice,
    validateRename,
    validateReassign,
}