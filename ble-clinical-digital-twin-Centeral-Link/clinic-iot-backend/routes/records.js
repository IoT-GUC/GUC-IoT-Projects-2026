const { Router } = require("express");
const {
    getHourlyRecordsCount,
    getHourlyPatientsCount,
    getRouterHourlyTotalSessionsDuration,
} = require("../controllers/records");

const router = new Router();

router.get("/hourly-records", getHourlyRecordsCount);
router.get("/hourly-patients", getHourlyPatientsCount);
router.get("/hourly-sessions-duration", getRouterHourlyTotalSessionsDuration);

module.exports = router;
