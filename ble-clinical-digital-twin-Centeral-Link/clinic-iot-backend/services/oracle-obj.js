const objectStorage = require("oci-objectstorage");
const common = require("oci-common");
const path = require("path");

const provider = new common.ConfigFileAuthenticationDetailsProvider(
    path.join(__dirname, '.oci/config'),
    "DEFAULT"
);

const client = new objectStorage.ObjectStorageClient({
    authenticationDetailsProvider: provider
});

const namespaceName = process.env.OBJECT_STORAGE_NAMESPACE_NAME;
const bucketName = process.env.OBJECT_STORAGE_BUCKET_NAME;
const region = process.env.OBJECT_STORAGE_REGION;

async function uploadImage(fileBuffer, fileName, mimeType) {
    await client.putObject({
        namespaceName,
        bucketName,
        objectName: fileName,
        putObjectBody: fileBuffer,
        contentType: mimeType
    });

    return fileName;
}

async function getImage(objectName) {
    const response = await client.getObject({
        namespaceName,
        bucketName,
        objectName
    });

    return response;
}

async function createImagePAR(objectName) {
    const tomorrow = new Date();
    tomorrow.setHours(tomorrow.getHours() + 24);

    const response =
        await client.createPreauthenticatedRequest({
            namespaceName,
            bucketName,

            createPreauthenticatedRequestDetails: {
                name: `img-${Date.now()}`,
                objectName: objectName,
                accessType: "ObjectRead",
                timeExpires: tomorrow
            }
        });

    const uri = response.preauthenticatedRequest.accessUri;
    return `https://objectstorage.${region}.oraclecloud.com${uri}`
}

async function deleteImage(objectName) {
    await client.deleteObject({
        namespaceName,
        bucketName,
        objectName
    });
}



module.exports = {
    uploadImage,
    getImage,
    createImagePAR,
    deleteImage
};