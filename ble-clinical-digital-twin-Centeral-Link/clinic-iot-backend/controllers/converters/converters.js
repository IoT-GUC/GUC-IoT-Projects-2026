const uuidToBuffer = (uuid) => {
    const hex = uuid.replace(/-/g, '');
    return Buffer.from(hex, 'hex');
};

const bufferToUuid = (buffer) => {
    const hex = buffer.toString('hex');
    return hex.replace(/(.{8})(.{4})(.{4})(.{4})(.{12})/, '$1-$2-$3-$4-$5');
};

const arrToBuffer = (arr) => {
    return Buffer.from(arr);
};

module.exports = {
    uuidToBuffer,
    bufferToUuid,
    arrToBuffer
};