function validateSignup(req, res, next) {
    const { hospital_id, name, address, admin_name, admin_email, password } = req.body;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!hospital_id || !name || !address || !admin_name || !admin_email || !password) {
        return res.status(400).json({ message: "All fields are required" });
    }
    if (typeof hospital_id !== "string" || typeof name !== "string" ||
        typeof address !== "string" || typeof admin_name !== "string" ||
        typeof admin_email !== "string" || typeof password !== "string") {
        return res.status(400).json({ message: "All fields must be strings" });
    }
    if (hospital_id.length < 3) {
        return res.status(400).json({ message: "Hospital ID must be at least 3 characters long" });
    }
    if (hospital_id.length > 20) {
        return res.status(400).json({ message: "Hospital ID must be less than 20 characters long" });
    }
    if (password.length < 6) {
        return res.status(400).json({ message: "Password must be at least 6 characters long" });
    }
    if (password.length > 100) {
        return res.status(400).json({ message: "Password must be less than 100 characters long" });
    }
    if (!emailRegex.test(admin_email)) {
        return res.status(400).json({ error: 'Admin email must be a valid email address' });
    }
    if (admin_email.length > 100) {
        return res.status(400).json({ message: "Email must be less than 100 characters long" });
    }
    if (name.length < 2) {
        return res.status(400).json({ message: "Name must be at least 2 characters long" });
    }
    if (name.length > 50) {
        return res.status(400).json({ message: "Name must be less than 50 characters long" });
    }
    if (admin_name.length < 2) {
        return res.status(400).json({ message: "Admin name must be at least 2 characters long" });
    }
    if (admin_name.length > 50) {
        return res.status(400).json({ message: "Admin name must be less than 50 characters long" });
    }
    if (address.length < 2) {
        return res.status(400).json({ message: "Address must be at least 2 characters long" });
    }
    if (address.length > 100) {
        return res.status(400).json({ message: "Address must be less than 100 characters long" });
    }
    next();
};

module.exports = {
    validateSignup,
};