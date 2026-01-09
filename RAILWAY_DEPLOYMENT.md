# Railway.app Deployment Guide - ComplianceVault

Complete guide to deploying ComplianceVault on Railway.app with persistent SQLite storage.

## ⚠️ Important: Railway Free Tier

Railway offers **$5 in free trial credits** valid for 30 days. After the trial, there's a $1/month free credit tier (very limited).  
**Best for**: Testing and short-term deployments.

---

## Step 1: Prepare Your Project

Ensure your GitHub repository is ready:
- ✅ All code pushed to GitHub
- ✅ `requirements.txt` exists in the root
- ✅ `.python-version` file exists (Railway will auto-detect Python 3.11)

---

## Step 2: Create Railway Account & New Project

1. Go to **[railway.app](https://railway.app)**
2. Click **"Login"** and sign in with your **GitHub account**
3. Click **"New Project"** (top right)
4. Select **"Deploy from GitHub repo"**
5. **Authorize Railway** to access your GitHub repositories
6. Select **`ComplianceVault`** from the list
7. Railway will automatically start building your project

---

## Step 3: Monitor Initial Build

Railway will:
- Auto-detect Python from `.python-version`
- Install dependencies from `requirements.txt`
- Try to start the application

**Expected**: The first deployment may fail or not be accessible because:
- No environment variables are set yet
- No persistent storage for SQLite is configured

---

## Step 4: Add Persistent Volume (Critical for SQLite)

Without this, your database will be **deleted every time you redeploy**!

1. Go to your **service** on the Railway dashboard
2. Click the **"Settings"** tab (or right-click on canvas → **"Add Volume"**)
3. Click **"+ Volume"** button
4. Set **Mount Path** to: `/app/data`
5. Click **"Add"**

> **Why `/app/data`?** Railway uses Nixpacks which places your app in `/app`. This ensures the database is saved in a persistent location.

---

## Step 5: Configure Environment Variables

1. Click on your **service** in the Railway dashboard
2. Go to the **"Variables"** tab
3. Click **"+ New Variable"** and add these **three** variables:

| Variable Name | Value |
|:---|:---|
| `DATABASE_URL` | `sqlite:////app/data/compliance_vault.db` |
| `SECRET_KEY` | `[YourRandomSecretKey123456]` |
| `DEBUG` | `False` |

> **Note**: Use 4 slashes `////` in the DATABASE_URL for absolute path.

4. **Save** the variables

---

## Step 6: Redeploy the Service

1. Go to **"Deployments"** tab
2. Click **"Deploy"** (or Railway will auto-deploy when you save variables)
3. Wait for the build to complete (watch the logs)
4. Look for: `✅ Deployment successful`

---

## Step 7: Generate Public URL

1. Go to **"Settings"** tab
2. Scroll to **"Networking"** section
3. Click **"Generate Domain"**
4. Railway will give you a URL like: `https://compliancevault-production.up.railway.app`

**Copy this URL** - you'll need it for the frontend!

---

## Step 8: Test the Backend

Open your browser and visit:
```
https://your-railway-url.railway.app/docs
```

You should see the **FastAPI Swagger Documentation** page.

---

## Step 9: Update Frontend to Connect

1. Open `frontend/js/api.js` on your local machine
2. Find the line with `const BASE_URL`
3. Change it to your Railway URL:
   ```javascript
   const BASE_URL = 'https://your-railway-url.railway.app/api';
   ```
4. **Save and push to GitHub**:
   ```powershell
   git add frontend/js/api.js
   git commit -m "Connect frontend to Railway backend"
   git push origin main
   ```

---

## Step 10: Deploy Frontend (GitHub Pages)

1. Go to your GitHub repository **Settings**
2. Click **"Pages"** in the left sidebar
3. Under **"Source"**, select:
   - **Branch**: `main`
   - **Folder**: `/ (root)`
4. Click **"Save"**
5. GitHub will give you a URL like: `https://yourusername.github.io/ComplianceVault/frontend/`

**Access your app at that URL!**

---

## Step 11: Custom Domain (Optional - GoDaddy)

If you want to use `compliance.azbers.com`:

### For Backend (Railway):
1. In Railway **Settings** → **Networking** → **Custom Domain**
2. Enter: `api.azbers.com`
3. Railway will provide a CNAME record value
4. Go to **GoDaddy DNS Settings** and add:
   - **Type**: CNAME
   - **Name**: api
   - **Value**: [Railway's CNAME]

### For Frontend (GitHub Pages):
1. In GitHub **Settings** → **Pages** → **Custom Domain**
2. Enter: `compliance.azbers.com`
3. Go to **GoDaddy DNS Settings** and add:
   - **Type**: CNAME  
   - **Name**: compliance
   - **Value**: `yourusername.github.io`

---

## Troubleshooting

### Database not persisting
- **Check**: Volume mount path is `/app/data`
- **Check**: `DATABASE_URL` uses `/app/data/compliance_vault.db`

### "Permission denied" errors
- Add environment variable: `RAILWAY_RUN_UID=0`

### App not starting
- Check **Deployment Logs** for errors
- Verify all 3 environment variables are set correctly

---

## 🎉 You're Live!

Your ComplianceVault platform is now hosted professionally on Railway.app with:
- ✅ Secure HTTPS
- ✅ Persistent database storage
- ✅ Auto-deploys on every Git push
- ✅ Professional URL (or custom domain)

**Login credentials:**
- Email: `admin@compliancevault.pro`
- Password: `Admin123!`
