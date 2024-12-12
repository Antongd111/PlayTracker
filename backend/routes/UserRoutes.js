const express = require('express');
const { register, login, protectedRoute } = require('../controllers/UserController');
const { authenticateToken } = require('../middleware/authMiddleware');

const router = express.Router();

router.post('/register', register); // Register a new user
router.post('/login', login); // Login user
router.get('/protected', authenticateToken, protectedRoute); // Protected route

module.exports = router;