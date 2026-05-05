const { Router } = require('express');
const { getAllPatients, getPatientSessions, insertPatient } = require('../controllers/patients');
const { validatePatient } = require('../controllers/validators/patients');
const router = Router();

router.get('/', getAllPatients);
router.get('/:id/sessions', getPatientSessions);
router.post('/', validatePatient, insertPatient);

module.exports = router;