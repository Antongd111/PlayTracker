const express = require('express');
const { register, login, protectedRoute } = require('../controllers/UserController');
const { authenticateToken } = require('../middleware/authMiddleware');

const router = express.Router();

router.post('/register', register); // Registrar usuario
router.post('/login', login); // Iniciar sesión
router.get('/protected', authenticateToken, protectedRoute); // Ruta protegida

module.exports = router;