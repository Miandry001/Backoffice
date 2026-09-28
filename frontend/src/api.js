// API configuration
// Uses VITE_API_URL environment variable if set, otherwise uses relative path (for Vite proxy in dev)
export const API_URL = import.meta.env.VITE_API_URL || ''

// Helper function to make API calls with credentials
export const apiFetch = (url, options = {}) => {
  return fetch(`${API_URL}${url}`, {
    ...options,
    credentials: 'include'
  })
}
