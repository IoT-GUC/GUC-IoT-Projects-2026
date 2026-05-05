function validateSettings(req, res, next) {
    const { name, address, admin_name, admin_email, password } = req.body;
    if (name) {
        if (typeof name !== 'string' || name.trim() === '') {
            return res.status(400).json({ error: 'Name must be a non-empty string' });
        }
        if (name.trim().length < 2 || name.length > 50) {
            return res.status(400).json({ error: 'Name must be between 2 and 50 characters' });
        }
    }
    if (address) {
        if (typeof address !== 'string' || address.trim() === '') {
            return res.status(400).json({ error: 'Address must be a non-empty string' });
        }
        if (address.trim().length < 2 || address.length > 100) {
            return res.status(400).json({ error: 'Address must be between 2 and 100 characters' });
        }
    }
    if (admin_name) {
        if (typeof admin_name !== 'string' || admin_name.trim() === '') {
            return res.status(400).json({ error: 'Admin name must be a non-empty string' });
        }
        if (admin_name.trim().length < 2 || admin_name.length > 50) {
            return res.status(400).json({ error: 'Admin name must be between 2 and 50 characters' });
        }
    }
    if (admin_email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(admin_email)) {
            return res.status(400).json({ error: 'Admin email must be a valid email address' });
        }
        if (admin_email.length > 100) {
            return res.status(400).json({ error: 'Admin email must be less than 100 characters' });
        }
    }
    if (password) {
        if (typeof password !== 'string' || password.trim() === '') {
            return res.status(400).json({ error: 'Password must be a non-empty string' });
        }
        if (password.trim().length < 6 || password.length > 100) {
            return res.status(400).json({ error: 'Password must be between 6 and 100 characters' });
        }
    }
    next();
}