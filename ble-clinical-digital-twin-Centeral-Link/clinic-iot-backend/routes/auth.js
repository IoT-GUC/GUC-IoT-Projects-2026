const { Router } = require("express");
const { signup, login } = require("../controllers/auth");
const { validateSignup } = require("../controllers/validators/auth");

const router = new Router();

router.post("/signup", validateSignup, signup);
router.post("/login", login);

module.exports = router;