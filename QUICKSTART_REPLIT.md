# Quick Start: Free Replit Deployment in 5 Minutes

No credit card. No payment. Just deploy.

---

## BEFORE YOU START

- [ ] You have a GitHub account
- [ ] Your code is pushed to GitHub
- [ ] You're ready in 5 minutes

---

## STEP-BY-STEP CHECKLIST

### 1️⃣ Go to Replit (1 minute)

- [ ] Open https://replit.com
- [ ] Click "Sign up" (top right)
- [ ] Choose "Sign up with GitHub" 
- [ ] You're in ✓

### 2️⃣ Import Your Repository (1 minute)

- [ ] Click the "+" button (Create)
- [ ] Select "Import from GitHub"
- [ ] Paste: `https://github.com/yourusername/WorkshopApril7To10`
- [ ] Click "Import"
- [ ] Wait for environment setup (30 seconds)
- [ ] You see the code editor ✓

### 3️⃣ Update Requirements (1 minute)

**In the Replit editor file browser:**

- [ ] Find `backend/requirements.txt`
- [ ] Replace with contents from `backend/requirements-replit.txt`
  - (Copy the minimal version from that file)
- [ ] Save (Ctrl+S or Cmd+S)

Or simpler: Just keep it as-is and Replit will install what's needed.

### 4️⃣ Run It (1 minute)

- [ ] Click the big "Run" button (top center)
- [ ] Wait 30-60 seconds for first install
- [ ] See terminal output: `Running on http://0.0.0.0:5000`
- [ ] Running ✓

### 5️⃣ Get Your URL (1 minute)

- [ ] Look at the "Webview" on the right side
- [ ] Click "Open in new tab" icon
- [ ] Browser opens → Your URL is in address bar
- [ ] **Example:** `https://orbital-dynamics-abc123.replit.dev`
- [ ] Copy this URL! 📋

---

## DONE! 🎉

Your deployment is live and public. You can:

✅ Share the URL with anyone  
✅ Use it for 7+ days free  
✅ No credit card ever asked  
✅ All features working (except heavy 3D)  

---

## TEST IT WORKS

### Test 1: Frontend Loads
- [ ] Go to your Replit URL in browser
- [ ] See the "Orbital Dynamics" homepage
- [ ] Click around sections

### Test 2: API Works
- [ ] Open browser DevTools (F12)
- [ ] Go to Console tab
- [ ] Paste this:
```javascript
fetch('https://YOUR-REPLIT-NAME.replit.dev/api/health')
  .then(r => r.json())
  .then(d => console.log(d));
```
- [ ] See JSON response with `"status": "ok"`

### Test 3: Try TLE Parsing
- [ ] Go to "TLE Understanding" section in UI
- [ ] ISS TLE should be pre-filled
- [ ] Click "Parse TLE"
- [ ] See results populate

---

## SHARE WITH TEAM

Send them your URL:
```
https://YOUR-REPLIT-NAME.replit.dev
```

They can:
- ✅ View from any browser
- ✅ No installation needed
- ✅ Try all features live
- ✅ Perfect for demos

---

## WHAT IF SOMETHING BREAKS?

### "Run" button does nothing
**Fix:** Click it again or refresh browser

### Timeout error
**Fix:** Wait longer (first install is slow ~60 seconds)

### API error or 404
**Fix:** Code might have an error. Check Replit terminal for red error text. Share the error with me.

### "Cannot find module"
**Fix:** In Replit terminal, type:
```
pip install -r backend/requirements.txt
```
Then click "Run" again

---

## KEEP IT ALIVE AFTER 7 DAYS

Replit keeps free tier projects alive as long as you **access them within 7 days**.

To keep yours active:
- [ ] Visit the URL once per week
- [ ] Or click "Run" button in Replit weekly
- [ ] That's it!

---

## NEXT STEPS

### Now That You Have a Live URL

1. **For interviews:** Share URL with your interviewer - "Here's my orbital dynamics platform working live!"
2. **For your team:** Share link in Slack/email for demos
3. **For testing:** Use it to validate all features before paid deployment

### Paid Deployment (Later)

When you need it beyond 7 days/want always-on, see [DEPLOYMENT.md](../DEPLOYMENT.md):
- AWS EC2: $0-30/month
- Replit Paid: $7/month
- DigitalOcean: $5-12/month

---

## THAT'S IT! 

Your free, public, production-ready deployment is live.

**URL to share:** https://YOUR-REPLIT-NAME.replit.dev

Go get 'em! 🚀
