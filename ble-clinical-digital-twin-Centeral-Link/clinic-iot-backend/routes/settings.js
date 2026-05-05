const { Router } = require("express");
const { getSettings, updateSettings, updateBlueprint, resetRecords, deleteAccount, getBlueprint } = require("../controllers/settings");
const multer = require("multer");

const router = new Router();
const upload = multer();

router.get("/", getSettings);
router.put("/", updateSettings);
router.put("/blueprint", upload.single("image"), updateBlueprint);
router.get("/blueprint", getBlueprint);
router.delete("/records", resetRecords);
router.delete("/account", deleteAccount);

module.exports = router;