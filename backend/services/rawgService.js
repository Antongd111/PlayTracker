const axios = require('axios');

const apiKey = process.env.RAWG_API_KEY;
const baseUrl = process.env.RAWG_BASE_URL;

const rawgService = {
  
    // Get games from RAWG
    async getGames(query = '', page = 1) {
    try {
        const response = await axios.get(`${baseUrl}/games`, {
        params: {
            key: apiKey,
            search: query,
            page: page,
        },
        });
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data || 'Error fetching games from RAWG API');
    }
    },
};

module.exports = rawgService;