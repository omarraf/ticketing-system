/**
 * API service for backend communication
 * Handles all HTTP requests to the Lambda backend via API Gateway
 */
import axios from 'axios';

// API base URL from environment variable
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status}`, response.data);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * Get all events
 * @returns {Promise<Array>} List of events
 */
export const getEvents = async () => {
  try {
    const response = await api.get('/events');
    return response.data.events || [];
  } catch (error) {
    console.error('Error fetching events:', error);
    throw error;
  }
};

/**
 * Get seat map for an event
 * @param {string} eventId - Event ID
 * @returns {Promise<Object>} Seat map data
 */
export const getSeats = async (eventId) => {
  try {
    const response = await api.get(`/events/${eventId}/seats`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching seats for event ${eventId}:`, error);
    throw error;
  }
};

/**
 * Reserve a seat
 * @param {Object} reservationData - Reservation details
 * @param {string} reservationData.event_id - Event ID
 * @param {string} reservationData.seat_id - Seat ID
 * @param {string} reservationData.user_id - User ID
 * @param {string} [reservationData.email] - User email (optional)
 * @returns {Promise<Object>} Reservation response
 */
export const reserveSeat = async (reservationData) => {
  try {
    const response = await api.post('/reserve', reservationData);
    return response.data;
  } catch (error) {
    // Handle specific error cases
    if (error.response?.status === 409) {
      throw new Error(error.response.data.message || 'Seat is no longer available');
    }
    if (error.response?.status === 400) {
      throw new Error(error.response.data.message || 'Invalid reservation request');
    }
    console.error('Error reserving seat:', error);
    throw error;
  }
};

export default api;
