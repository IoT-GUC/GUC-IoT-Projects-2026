const { Router } = require("express");
const {
    getHourlyRecordsCount,
    getHourlyPatientsCount,
    getRouterHourlyTotalSessionsDuration,
    getRoomsHourlyOccupancy,
    getRoomsDwellTime,
    getPatientsRoomStats,
    getAvgVisitTime,
} = require("../controllers/records");

const router = new Router();

router.get("/hourly-records",          getHourlyRecordsCount);
router.get("/hourly-patients",         getHourlyPatientsCount);
router.get("/hourly-sessions-duration",getRouterHourlyTotalSessionsDuration);

// Per-room analytics
router.get("/rooms-hourly-occupancy",  getRoomsHourlyOccupancy);
router.get("/rooms-dwell-time",        getRoomsDwellTime);
router.get("/patients-room-stats",     getPatientsRoomStats);

// Today's average visit time
router.get("/avg-visit-time",          getAvgVisitTime);

module.exports = router;
