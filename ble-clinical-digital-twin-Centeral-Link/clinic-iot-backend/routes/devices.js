const { Router } = require("express");
const { getAllDevices, getAllDevicesWithRoutersInfo, insertDevice, releaseDevice } = require("../controllers/devices");
const { validateDevice } = require("../controllers/validators/devices");

const router = new Router();

router.get("/", getAllDevices);
router.get("/with-routers-info", getAllDevicesWithRoutersInfo);
router.post("/", validateDevice, insertDevice);
router.put("/:id/release", releaseDevice);

module.exports = router;
