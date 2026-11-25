// Vercel serves the frontend and Flask API on one origin. Use localhost for
// local development when the frontend and backend run on separate ports.
const isLocal = ['localhost', '127.0.0.1'].includes(window.location.hostname);
window.CAMPUS_CONNECT_API = isLocal ? 'http://localhost:5000' : '';
