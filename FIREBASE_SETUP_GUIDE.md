# 🚀 Firebase Setup & Deployment Guide

## Step-by-Step Firebase Configuration

### Phase 1: Create Firebase Project (5 minutes)

#### 1.1 Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Create Project"**
3. Enter project name: `orbital-dynamics-isu`
4. Accept the default settings, click **"Create Project"**
5. Wait for project initialization to complete

#### 1.2 Enable Required Services

**Firestore Database:**
1. In Firebase Console, go to **Build → Firestore Database**
2. Click **"Create Database"**
3. Choose **"Start in test mode"** (for development)
4. Select region: **us-central1** (or closest to you)
5. Click **"Create"**

**Cloud Functions:**
1. Go to **Build → Functions**
2. Click **"Get Started"**
3. Follow the prompts (billing account required for production)

**Firebase Authentication:**
1. Go to **Build → Authentication**
2. Click **"Get Started"**
3. Enable providers:
   - **Google** → Click **"Enable"** → Select a project support email → **"Save"**
   - **GitHub** → Click **"Enable"** → (optional, skip if not needed)
   - **Email/Password** → Click **"Enable"** → **"Save"**

**Firebase Hosting:**
1. Go to **Build → Hosting**
2. Click **"Get Started"**
3. Follow the CLI setup instructions (next step)

**Cloud Storage:**
1. Go to **Build → Storage**
2. Click **"Get Started"**
3. Choose **"Start in test mode"**
4. Select region: **us-central1**
5. Click **"Done"**

---

### Phase 2: Local Environment Setup (10 minutes)

#### 2.1 Install Firebase CLI

```bash
# Install Node.js (if not already installed)
# Download from https://nodejs.org/ and install

# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login
```

#### 2.2 Get Firebase Configuration

1. In Firebase Console, go to **Project Settings** (gear icon)
2. Copy the **Project ID** (e.g., `orbital-dynamics-isu`)
3. In your project root, update `.firebaserc`:

```json
{
  "projects": {
    "default": "orbital-dynamics-isu"
  }
}
```

#### 2.3 Get Firebase Web Config

1. In Firebase Console, go to **Project Settings**
2. Scroll down to **"Your apps"** section
3. Click **"</>" (Web)** to add a web app if not already added
4. Copy the Firebase config object
5. Open `frontend/public/firebase-config.js`
6. Replace `YOUR_*` placeholders with actual values:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",                    // From Firebase Console
  authDomain: "orbital-dynamics-isu.firebaseapp.com",
  projectId: "orbital-dynamics-isu",
  storageBucket: "orbital-dynamics-isu.appspot.com",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID"
};
```

---

### Phase 3: Deploy Cloud Functions Backend (15 minutes)

#### 3.1 Prepare Functions

The Python Cloud Functions are located in `backend/functions/`:

```
backend/functions/
├── main.py              # Main function handler
├── requirements.txt     # Python dependencies
└── orbital_modules/     # (Copy of backend/orbital_mechanics/ modules)
```

#### 3.2 Copy Orbital Mechanics Modules

Copy all modules from `backend/orbital_mechanics/` to `backend/functions/orbital_modules/`:

```bash
# Windows PowerShell
Copy-Item -Path "backend/orbital_mechanics/*" -Destination "backend/functions/orbital_modules/" -Recurse -Force

# macOS/Linux
cp -r backend/orbital_mechanics/* backend/functions/orbital_modules/
```

#### 3.3 Deploy Functions

```bash
# From project root directory
firebase deploy --only functions

# Or for specific function
firebase deploy --only functions:orbitalDynamicsAPI
```

**Expected output:**
```
✓  Function URL: https://us-central1-orbital-dynamics-isu.cloudfunctions.net/orbitalDynamicsAPI
```

Save this URL! Your frontend will use it.

---

### Phase 4: Deploy Frontend (10 minutes)

#### 4.1 Update Firebase Config in Frontend

In `firebase-config.js`, verify the `API_BASE_URL` construction:

```javascript
// This is already in the code, but verify it matches your Cloud Function URL
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
  APIs_BASE_URL = 'http://localhost:5000/api';  // Local dev
} else {
  const projectId = firebaseConfig.projectId;
  API_BASE_URL = `https://us-central1-${projectId}.cloudfunctions.net/orbitalDynamicsAPI/api`;
}
```

#### 4.2 Deploy to Firebase Hosting

```bash
# Build (if applicable)
# npm run build  (if using build tools)

# Deploy
firebase deploy --only hosting

# Or deploy everything
firebase deploy
```

**Expected output:**
```
✓  Deploy complete!
✓  Hosting URL: https://orbital-dynamics-isu.web.app
```

Your site is now live! 🎉

---

### Phase 5: Configure Firestore Security Rules (5 minutes)

#### 5.1 Set Up Security Rules

1. In Firebase Console, go to **Firestore Database**
2. Click **"Rules"** tab
3. Replace with these rules:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // PUBLIC: Read-only orbit catalog
    match /public/orbits/{doc=**} {
      allow read: if true;
      allow write: if false;
    }
    
    // USERS: Can read/write their own scenarios
    match /users/{userId}/scenarios/{document=**} {
      allow read, write: if request.auth.uid == userId;
    }
    
    // USERS: User profile info
    match /users/{userId} {
      allow read, write: if request.auth.uid == userId;
    }
    
    // DENY everything else by default
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

4. Click **"Publish"**

---

### Phase 6: Test Local Development (5 minutes)

#### 6.1 Run Firebase Emulator Suite

```bash
# Install emulator (first time only)
firebase emulators:start

# Output will show:
# ✓ Firestore Emulator running on 127.0.0.1:8080
# ✓ Auth Emulator running on 127.0.0.1:9099
```

#### 6.2 Start Local Frontend Server

In another terminal:

```bash
cd frontend/public
python -m http.server 8000
# OR
npx http-server
```

#### 6.3  Test in Browser

Navigate to: `http://localhost:8000`

Test:
- [ ] Home page loads
- [ ] Sign In button appears
- [ ] Click "Sign In" → Google/GitHub login works
- [ ] Email signup works
- [ ] Parse TLE section works
- [ ] 3D visualization loads

---

## 🔐 Firestore Schema

### Collections Structure

```
firestore:
├── public/
│   └── orbits/
│       ├── leo { name, description, ... }
│       ├── geo { name, description, ... }
│       └── ...
│
├── users/
│   └── {userId}
│       ├── profile {displayName, email, photoURL, ...}
│       └── scenarios/
│           ├── {scenarioId}
│           │   ├── name: string
│           │   ├── data: object
│           │   ├── created_at: timestamp
│           │   └── updated_at: timestamp
│           └── ...
```

---

## 🚀 Deployment Checklist

### Development
- [ ] Firebase project created
- [ ] All services enabled (Firestore, Functions, Auth, Hosting, Storage)
- [ ] Firebase CLI installed and logged in
- [ ] `.firebaserc` configured
- [ ] `firebase-config.js` updated with real credentials
- [ ] Orbital mechanics modules copied to `backend/functions/orbital_modules/`
- [ ] Local emulator runs: `firebase emulators:start`
- [ ] Frontend loads locally and can make API calls

### Production
- [ ] Cloud Functions deployed: `firebase deploy --only functions`
- [ ] Firestore Security Rules published
- [ ] Frontend deployed: `firebase deploy --only hosting`
- [ ] Test all endpoints:
  - TLE parsing
  - Keplerian conversions
  - Hohmann transfers
  - Orbit catalog listing
- [ ] Authentication working (Google, GitHub, Email)
- [ ] User scenarios save to Firestore
- [ ] Performance good (< 3s initial load)

---

## 📊 Environment Variables

Create a `.env.local` file in the project root (for local development):

```env
# Firebase
REACT_APP_FIREBASE_API_KEY=your_api_key
REACT_APP_FIREBASE_AUTH_DOMAIN=orbital-dynamics-isu.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=orbital-dynamics-isu
REACT_APP_FIREBASE_STORAGE_BUCKET=orbital-dynamics-isu.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
REACT_APP_FIREBASE_APP_ID=your_app_id

# API
REACT_APP_API_BASE_URL=http://localhost:5000/api  # Local dev only
```

---

## 🆘 Troubleshooting

### "Functions missing module" error
**Solution**: Copy orbital mechanics modules:
```bash
Copy-Item -Path "backend/orbital_mechanics/*" -Destination "backend/functions/orbital_modules/" -Recurse
```

### "CORS error" when calling API
**Solution**: Make sure Cloud Functions has CORS headers (already included in `main.py`)

### "Firestore authentication error"
**Solution**: Check security rules and ensure user is logged in before saving scenarios

### "Firebase config not found"
**Solution**: Update `firebase-config.js` with real values from Firebase Console Project Settings

### "Cloud Functions timeout"
**Solution**: Increase timeout in `firebase.json`:
```json
{
  "functions": {
    "timeoutSeconds": 60
  }
}
```

---

## 📚 Additional Resources

- [Firebase Documentation](https://firebase.google.com/docs)
- [Cloud Functions Python Runtime](https://cloud.google.com/functions/docs/quickstart/deploy-http-function)
- [Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Firebase Hosting Guide](https://firebase.google.com/docs/hosting)
- [Firebase CLI Reference](https://firebase.google.com/docs/cli)

---

**Next Steps**: After successful deployment, user data and scenarios will persist in Firestore. The application now scales automatically with Firebase, supports multiple users, and provides real-time synchronization across devices! 🌍
