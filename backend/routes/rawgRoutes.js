const express = require('express');
const rawgService = require('../services/rawgService');

const router = express.Router();

// Get games endpoint
router.get('/rawg', async (req, res) => {
  const { q, page, pageSize, ordering } = req.query;

  try {
    const games = await rawgService.getGames({
      query: q || '',
      page: parseInt(page) || 1,
      pageSize: parseInt(pageSize) || 10,
      ordering: ordering || '',
    });
    res.status(200).json(games);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

module.exports = router;