const axios = require('axios');

const apiKey = process.env.RAWG_API_KEY;
const baseUrl = process.env.RAWG_BASE_URL;

const rawgService = {
  // Get games from RAWG with optional query and parameters
  async getGames({ query = '', page = 1, pageSize = 10, ordering = '' }) {
    try {
      const response = await axios.get(`${baseUrl}/games`, {
        params: {
          key: apiKey,
          search: query,
          page: page,
          page_size: pageSize,
          ordering: ordering,
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching games from RAWG API:', error.message);
      throw new Error(error.response?.data || 'Error fetching games from RAWG API');
    }
  },
};

module.exports = rawgService;