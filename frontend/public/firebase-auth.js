/**
 * Firebase Authentication Module
 * 
 * Handles user authentication with Google, GitHub, and email/password
 * Provides functions for login, logout, and session management
 */

class OrbitalAuth {
  constructor() {
    this.currentUser = null;
    this.firebaseReady = Boolean(window.__firebaseReady);
    this.initAuthListener();
  }

  /**
   * Listen for auth state changes
   */
  initAuthListener() {
    if (!this.firebaseReady) {
      this.updateAuthUI(false);
      return;
    }

    firebase.auth().onAuthStateChanged((user) => {
      this.currentUser = user;
      if (user) {
        console.log(`✅ User logged in: ${user.displayName || user.email}`);
        this.updateAuthUI(true);
        this.loadUserScenarios();
      } else {
        console.log('❌ User logged out');
        this.updateAuthUI(false);
      }
    });
  }

  /**
   * Sign in with Google
   */
  async signInWithGoogle() {
    if (!this.firebaseReady) {
      alert('Firebase Auth is not configured yet. Add valid keys in firebase-config.js.');
      throw new Error('Firebase Auth not configured');
    }

    try {
      const provider = new firebase.auth.GoogleAuthProvider();
      const result = await firebase.auth().signInWithPopup(provider);
      return result.user;
    } catch (error) {
      console.error('Google Sign-in failed:', error);
      alert(`Google Sign-in failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Sign in with GitHub
   */
  async signInWithGitHub() {
    if (!this.firebaseReady) {
      alert('Firebase Auth is not configured yet. Add valid keys in firebase-config.js.');
      throw new Error('Firebase Auth not configured');
    }

    try {
      const provider = new firebase.auth.GithubAuthProvider();
      const result = await firebase.auth().signInWithPopup(provider);
      return result.user;
    } catch (error) {
      console.error('GitHub Sign-in failed:', error);
      alert(`GitHub Sign-in failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Sign up with email and password
   */
  async signUpWithEmail(email, password) {
    if (!this.firebaseReady) {
      alert('Firebase Auth is not configured yet. Add valid keys in firebase-config.js.');
      throw new Error('Firebase Auth not configured');
    }

    try {
      const result = await firebase.auth().createUserWithEmailAndPassword(email, password);
      return result.user;
    } catch (error) {
      console.error('Email Sign-up failed:', error);
      alert(`Sign-up failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Sign in with email and password
   */
  async signInWithEmail(email, password) {
    if (!this.firebaseReady) {
      alert('Firebase Auth is not configured yet. Add valid keys in firebase-config.js.');
      throw new Error('Firebase Auth not configured');
    }

    try {
      const result = await firebase.auth().signInWithEmailAndPassword(email, password);
      return result.user;
    } catch (error) {
      console.error('Email Sign-in failed:', error);
      alert(`Sign-in failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Sign out current user
   */
  async signOut() {
    if (!this.firebaseReady) {
      return;
    }

    try {
      await firebase.auth().signOut();
      this.currentUser = null;
      console.log('Signed out successfully');
    } catch (error) {
      console.error('Sign-out failed:', error);
      throw error;
    }
  }

  /**
   * Get current user
   */
  getCurrentUser() {
    return this.currentUser;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return this.currentUser !== null;
  }

  /**
   * Save scenario to Firestore
   */
  async saveScenario(scenarioName, scenarioData) {
    if (!this.firebaseReady) {
      throw new Error('Firebase is not configured');
    }

    if (!this.currentUser) {
      throw new Error('User must be logged in to save scenarios');
    }

    try {
      const docRef = await db.collection(`users/${this.currentUser.uid}/scenarios`).add({
        name: scenarioName,
        data: scenarioData,
        created_at: firebase.firestore.FieldValue.serverTimestamp(),
        updated_at: firebase.firestore.FieldValue.serverTimestamp()
      });

      console.log(`✅ Scenario saved: ${docRef.id}`);
      return docRef.id;
    } catch (error) {
      console.error('Failed to save scenario:', error);
      throw error;
    }
  }

  /**
   * Load user's saved scenarios
   */
  async loadUserScenarios() {
    if (!this.firebaseReady || !this.currentUser) return [];

    try {
      const snapshot = await db.collection(`users/${this.currentUser.uid}/scenarios`).get();
      const scenarios = [];
      snapshot.forEach((doc) => {
        scenarios.push({
          id: doc.id,
          ...doc.data()
        });
      });

      console.log(`📥 Loaded ${scenarios.length} scenarios`);
      return scenarios;
    } catch (error) {
      console.error('Failed to load scenarios:', error);
      return [];
    }
  }

  /**
   * Delete scenario
   */
  async deleteScenario(scenarioId) {
    if (!this.firebaseReady) {
      throw new Error('Firebase is not configured');
    }

    if (!this.currentUser) {
      throw new Error('User must be logged in');
    }

    try {
      await db.collection(`users/${this.currentUser.uid}/scenarios`).doc(scenarioId).delete();
      console.log(`🗑️  Scenario deleted: ${scenarioId}`);
    } catch (error) {
      console.error('Failed to delete scenario:', error);
      throw error;
    }
  }

  /**
   * Update auth UI based on login state
   */
  updateAuthUI(isLoggedIn) {
    const authSection = document.getElementById('auth-section');
    if (!authSection) return;

    if (isLoggedIn) {
      authSection.innerHTML = `
        <div class="auth-status logged-in">
          <span>👤 ${this.currentUser.displayName || this.currentUser.email}</span>
          <button class="btn btn-sm btn-outline-danger" onclick="orbitalAuth.signOut()">
            Sign Out
          </button>
        </div>
      `;
    } else {
      authSection.innerHTML = `
        <div class="auth-status logged-out">
          ${this.firebaseReady
            ? '<button class="btn btn-sm btn-primary" onclick="showAuthModal()">Sign In</button>'
            : '<span title="Set valid Firebase keys in firebase-config.js">Auth disabled: configure Firebase</span>'}
        </div>
      `;
    }
  }
}

// Initialize auth object
const orbitalAuth = new OrbitalAuth();

/**
 * Show authentication modal
 */
function showAuthModal() {
  const modal = document.getElementById('auth-modal');
  if (!modal) {
    createAuthModal();
  }
  document.getElementById('auth-modal').style.display = 'block';
}

/**
 * Hide authentication modal
 */
function hideAuthModal() {
  document.getElementById('auth-modal').style.display = 'none';
}

/**
 * Create authentication modal if it doesn't exist
 */
function createAuthModal() {
  const modal = document.createElement('div');
  modal.id = 'auth-modal';
  modal.className = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h3>Sign In to Orbital Dynamics</h3>
        <button class="btn-close" onclick="hideAuthModal()">&times;</button>
      </div>

      <div class="modal-body">
        <!-- Social Login -->
        <div class="auth-methods">
          <button class="btn btn-block btn-oauth google" onclick="orbitalAuth.signInWithGoogle()">
            <span class="icon">🔵</span> Sign in with Google
          </button>
          <button class="btn btn-block btn-oauth github" onclick="orbitalAuth.signInWithGitHub()">
            <span class="icon">⬛</span> Sign in with GitHub
          </button>
        </div>

        <div class="divider">Or</div>

        <!-- Email/Password -->
        <form id="email-auth-form">
          <div class="form-group mb-3">
            <label for="auth-email">Email:</label>
            <input type="email" class="form-control" id="auth-email" placeholder="your@email.com" required>
          </div>
          <div class="form-group mb-3">
            <label for="auth-password">Password:</label>
            <input type="password" class="form-control" id="auth-password" placeholder="••••••••" required>
          </div>
          <div class="form-check mb-3">
            <input class="form-check-input" type="checkbox" id="auth-signup" value="">
            <label class="form-check-label" for="auth-signup">
              I don't have an account (Sign up instead)
            </label>
          </div>
          <button type="submit" class="btn btn-primary w-100">
            Sign In / Sign Up
          </button>
        </form>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // Handle email auth form
  document.getElementById('email-auth-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    const isSignUp = document.getElementById('auth-signup').checked;

    try {
      if (isSignUp) {
        await orbitalAuth.signUpWithEmail(email, password);
      } else {
        await orbitalAuth.signInWithEmail(email, password);
      }
      hideAuthModal();
    } catch (error) {
      console.error('Auth error:', error);
    }
  });
}
