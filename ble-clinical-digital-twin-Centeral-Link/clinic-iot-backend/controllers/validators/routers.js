const { validate } = require('uuid');

function validateRouter(req, res, next) {
    const { router_id,name, location_x, location_y } = req.body;
    if (!router_id || !name || !location_x || !location_y) {
        return res.status(400).json({ message: "All fields are required" });
    }
    if (!validate(router_id)) {
        return res.status(400).json({ message: "Invalid router ID" });
    }
    if (typeof name !== "string" || name.trim().length < 2 || name.length > 100) {
        return res.status(400).json({ message: "Router name must be between 2 and 100 characters" });
    }
    if (typeof location_x !== "number" || typeof location_y !== "number") {
        return res.status(400).json({ message: "Location coordinates must be numbers" });
    }
    if (location_x < 0 || location_x > 1) {
        return res.status(400).json({ message: "Location X must be between 0 and 1" });
    }
    if (location_y < 0 || location_y > 1) {
        return res.status(400).json({ message: "Location Y must be between 0 and 1" });
    }
    next();
};

module.exports = {
    validateRouter,

}