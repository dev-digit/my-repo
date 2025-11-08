import axios from 'axios';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add request ID
apiClient.interceptors.request.use(
  (config) => {
    // Add unique request ID for tracking
    config.headers['X-Request-ID'] = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;

      if (status === 429) {
        error.message = 'Rate limit exceeded. Please wait before sending another message.';
      } else if (status === 401) {
        error.message = 'Authentication required. Please check your API credentials.';
      } else if (status === 500) {
        error.message = 'Server error. Please try again later.';
      } else if (data?.detail) {
        error.message = data.detail;
      }
    } else if (error.request) {
      // Network error
      error.message = 'Unable to connect to the server. Please check your connection.';
    }

    return Promise.reject(error);
  }
);

export { apiClient };