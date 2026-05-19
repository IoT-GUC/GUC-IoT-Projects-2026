// Validate
const isValidMac = (mac) =>
    /^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$/.test(mac);

// Generate
const generateMac = () =>
    Array.from({ length: 6 }, () =>
        Math.floor(Math.random() * 256).toString(16).padStart(2, '0')
    ).join(':');

module.exports = {
    isValidMac,
    generateMac,
};