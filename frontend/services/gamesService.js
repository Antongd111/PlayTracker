import api from './api';

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
