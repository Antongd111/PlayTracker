import api from './api';

/**
 * Send a login request to the backend with the provided email and password and return the session token if successful.
 * 
 * @param {*} email 
 * @param {*} password 
 * @returns 
 */
export const loginUser = async (email, password) => {
  try {
    const response = await api.post('users/login', { email, password });
    return response.data;
  } catch (error) {
    throw error;
  }
};
