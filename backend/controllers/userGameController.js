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

exports.updateGameStatus = async (req, res) => {
  const { userId, rawgGameId, status } = req.body;

  try {
    // Find the user game
    let userGame = await UserGame.findOne({ where: { userId, rawgGameId } });

    if (userGame) {
      if (status === "notSaved") {
        // Delete the game if status is "notSaved"
        await userGame.destroy();
        res.status(200).json({ message: 'Game removed successfully.' });
      } else {
        // Update the status if the game is already associated with the user
        userGame.status = status;
        await userGame.save();
        res.status(200).json({ message: 'Game status updated successfully.' });
      }
    } else {
      if (status === "notSaved") {
        res.status(400).json({ message: 'Cannot remove a game that is not associated with the user.' });
      } else {
        // Create a new association if the game is not associated with the user
        title = "";
        userGame = await UserGame.create({ userId, rawgGameId, title, status });
        res.status(201).json({ message: 'Game added and status set successfully.' });
      }
    }
  } catch (error) {
    console.error('Error adding or updating game status:', error);
    res.status(500).json({ message: 'Error adding or updating game status', error: error.message });
  }
};