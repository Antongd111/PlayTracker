const express = require('express');
const router = express.Router();
const { getUserGames, updateGameStatus } = require('../controllers/userGameController');
// const { searchGames } = require('../controllers/gameController'); // Para futuras rutas de búsqueda

router.get('/userGames/details/:userId', getUserGames);
router.post('/updateStatus', updateGameStatus);
// router.get('/search', searchGames);

module.exports = router;
