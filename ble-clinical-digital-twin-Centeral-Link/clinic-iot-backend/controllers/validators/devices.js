const { validate } = require('uuid');

function validateDevice(req, res, next) {
    const { device_id,name } = req.body;
    if ( !device_id || !name || typeof name !== "string" || name.trim() === "") {
        return res.status(400).json({ message: "Invalid device name" });
    }
    if (!validate(device_id)) {
        return res.status(400).json({ message: "Invalid device ID" });
    }
    if (name.trim().length < 2 || name.length > 100) {
        return res.status(400).json({ message: "Device name must be between 2 and 100 characters" });
    }
    next();
};

module.exports = {
    validateDevice,
}