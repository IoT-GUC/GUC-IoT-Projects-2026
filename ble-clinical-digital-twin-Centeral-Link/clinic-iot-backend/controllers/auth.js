// controllers/auth.controller.js
const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");
const queries = require("./queries/auth")
const db = require("../services/oracle-db");
const oracledb = require("oracledb");
const JWT_SECRET = process.env.JWT_SECRET || "secret_key";

// REGISTER
async function signup(req, res) {
    try {
        const { hospital_id, name, address, admin_name, admin_email, password } = req.body;

        const response = await db.query(queries.selectHospitalId, { hospital_id: hospital_id }, { maxRows: 1 });
        if (response.error) {
            return res.status(500).json({ message: "Server error" });
        }
        if (response.rows.length > 0) {
            return res.status(400).json({ message: "Hospital ID already exists" });
        }

        const hashedPassword = await bcrypt.hash(password, 10);

        const newHospital = {
            hospital_id: hospital_id,
            name: name,
            address: address,
            admin_name: admin_name,
            admin_email: admin_email,
            password: hashedPassword,
            id: { type: oracledb.DB_TYPE_RAW, dir: oracledb.BIND_OUT },
        };

        const result = await db.query(queries.insertHospital, newHospital, { autoCommit: true });

        if (result.rowsAffected < 1) {
            return res.status(500).json({ message: "Failed to register hospital" });
        }

        const token = jwt.sign(
            { id: result.outBinds.id[0], hospital_id: hospital_id },
            JWT_SECRET,
            { expiresIn: "1h" }
        );

        res.status(201).json({ message: "Hospital registered successfully", token });
    } catch (err) {
        res.status(500).json({ message: "Server error" });
    }
};

// LOGIN
async function login(req, res) {
    try {
        const { hospital_id, password } = req.body;

        const response = await db.query(queries.selectHospitalByHospitalId, { hospital_id: hospital_id }, { maxRows: 1 });
        if (response.error || !response.rows.length) {
            return res.status(400).json({ message: "Invalid credentials" });
        }
        const hospital = response.rows[0];
        const isMatch = await bcrypt.compare(password, hospital.PASSWORD);
        if (!isMatch) {
            return res.status(400).json({ message: "Invalid credentials" });
        }

        const token = jwt.sign(
            { id: hospital.ID, hospital_id: hospital.HOSPITAL_ID },
            JWT_SECRET,
            { expiresIn: "1h" }
        );

        res.json({ token });
    } catch (err) {
        res.status(500).json({ message: "Server error" });
    }
};

module.exports = {
    signup,
    login,
};