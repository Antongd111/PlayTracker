const UserGame = require('../models/UserGame');
const axios = require('axios');

// Get all games for a user
exports.getUserGames = async (req, res) => {
  const { userId } = req.params;

  try {
    // Get the games for the user
    const userGames = await UserGame.findAll({ where: { userId } });

    if (!userGames.length) {
      return res.status(404).json({ message: 'No games found for this user.' });
    }

    // Realizar peticiones a la API de RAWG para cada juego
    const apiKey = process.env.RAWG_API_KEY;
    const gameDetailsPromises = userGames.map(async (game) => {
      const rawgResponse = await axios.get(`https://api.rawg.io/api/games/${game.rawgGameId}?key=${apiKey}`);
      return {
        ...game.toJSON(),
        rawgDetails: rawgResponse.data,
      };
    });

    // Wait until all the promises are resolved
    const gamesWithDetails = await Promise.all(gameDetailsPromises);

    res.status(200).json({ games: gamesWithDetails });
  } catch (error) {
    console.error('Error fetching user games:', error);
    res.status(500).json({ message: 'Error fetching user games', error: error.message });
  }
};