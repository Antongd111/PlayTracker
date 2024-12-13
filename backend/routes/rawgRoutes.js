const express = require('express');
const rawgService = require('../services/rawgService');

const router = express.Router();

// Get games endpoint
router.get('/rawg', async (req, res) => {
  const { query, page } = req.query;

  try {
    const games = await rawgService.getGames(query, page);
    res.status(200).json(games);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

module.exports = router;
