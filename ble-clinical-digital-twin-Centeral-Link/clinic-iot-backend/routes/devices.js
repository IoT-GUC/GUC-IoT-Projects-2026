const { Router } = require("express");
const { getAllDevices, getAllDevicesWithRoutersInfo, insertDevice, releaseDevice,
        renameDevice, reassignDevice } = require("../controllers/devices");
const { validateDevice, validateRename, validateReassign } = require("../controllers/validators/devices");

const router = new Router();

router.get("/", getAllDevices);
router.get("/with-routers-info", getAllDevicesWithRoutersInfo);
router.post("/", validateDevice, insertDevice);
router.put("/:id/release", releaseDevice);
router.patch("/:id/name", validateRename, renameDevice);
router.put("/:id/assign", validateReassign, reassignDevice);

module.exports = router;
