import api from './api';

/**
 * Add a game to the user with the provided userId.
 * 
 * @param {*} userId
 * @param {*} rawgGameId
 * @param {*} status
 * @returns 
 */

export const updateGameStatus = async (userId, rawgGameId, status) => {
  try {
    const response = await api.post('/games/updateStatus', {
      userId,
      rawgGameId,
      status,
    });
    return response.data;
  } catch (error) {
    throw error;
  }
}

/**
 * Get the games and their data for the user with the provided userId.
 * 
 * @param {*} userId 
 * @returns 
 */
export const getUserGames = async (userId) => {
  try {
    const response = await api.get(`/games/userGames/details/${userId}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Search games from the RAWG API with the provided query.
 * 
 * @param {*} query  The query to search for.
 * @param {*} page  The page number.
 * @param {*} pageSize  The number of games per page.
 * @param {*} ordering  The ordering of the games.
 * @returns 
 */
export const searchGames = async (query, page = 1, pageSize = 20, ordering = '') => {
  try {
    const response = await api.get('/rawg/search', {
      params: {
        q: query,
        page,
        pageSize,
        ordering,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error searching games:', error);
    throw error;
  }
};
