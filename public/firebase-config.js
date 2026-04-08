/**
 * Firebase Configuration & Initialization
 * 
 * This file initializes the Firebase SDK for use throughout the application.
 * Update the config with your Firebase project details from the Firebase Console.
 */

// Initialize Firebase (from Firebase Console)
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "orbital-dynamics-isu.firebaseapp.com",
  projectId: "orbital-dynamics-isu",
  storageBucket: "orbital-dynamics-isu.appspot.com",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID"
};

let app = null;
let auth = null;
let db = null;

function hasValidFirebaseConfig(config) {
  return Boolean(
    config &&
    config.apiKey &&
    !config.apiKey.startsWith('YOUR_') &&
    config.projectId &&
    config.appId &&
    !config.appId.startsWith('YOUR_')
  );
}

function inferProjectIdFromHostname(hostname) {
  if (!hostname) {
    return firebaseConfig.projectId;
  }

  if (hostname.endsWith('.web.app') || hostname.endsWith('.firebaseapp.com')) {
    return hostname.split('.')[0];
  }

  return firebaseConfig.projectId;
}

window.__firebaseReady = false;

if (typeof firebase !== 'undefined' && hasValidFirebaseConfig(firebaseConfig)) {
  // Initialize Firebase only when the config is complete.
  app = firebase.initializeApp(firebaseConfig);
  auth = firebase.auth();
  db = firebase.firestore();

  // Set Firestore settings for offline support.
  db.settings({
    cacheSizeBytes: firebase.firestore.CACHE_SIZE_UNLIMITED
  });

  window.__firebaseReady = true;
  console.log('🚀 Firebase initialized');
} else {
  console.warn('Firebase config is incomplete. Auth/Firestore features are disabled until valid keys are provided.');
}

/**
 * Get the API base URL based on environment
 * In production (Firebase Hosting), this automatically uses Cloud Functions
 */
let API_BASE_URL;
const hostname = window.location.hostname;

if (hostname === 'localhost' || hostname === '127.0.0.1') {
  // Local development: use local emulator or Flask
  API_BASE_URL = 'http://localhost:5000/api';
} else {
  // Production: use Firebase Cloud Functions
  const projectId = inferProjectIdFromHostname(hostname);
  API_BASE_URL = `https://us-central1-${projectId}.cloudfunctions.net/orbitalDynamicsAPI/api`;
}

console.log(`📡 API Base URL: ${API_BASE_URL}`);

/**
 * Simple fetch wrapper with error handling
 */
async function apiCall(endpoint, method = 'GET', data = null) {
  const options = {
    method: method,
    headers: {
      'Content-Type': 'application/json'
    }
  };
  
  if (data) {
    options.body = JSON.stringify(data);
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
