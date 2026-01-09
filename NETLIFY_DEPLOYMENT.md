# Netlify Deployment Guide - ComplianceVault Frontend

Complete guide to deploying your ComplianceVault frontend on Netlify while keeping your repository **private**.

---

## Why Netlify?

- ✅ **Deploy from private GitHub repos** (for free!)
- ✅ Automatic HTTPS & SSL certificates
- ✅ Custom domain support
- ✅ Auto-deploys on every Git push
- ✅ Lightning-fast CDN hosting
- ✅ Your code stays 100% secure and private

---

## Step 1: Sign Up for Netlify

1. Go to **[netlify.com](https://netlify.com)**
2. Click **"Sign up"**
3. Choose **"Sign up with GitHub"**
4. **Authorize Netlify** to access your GitHub account

---

## Step 2: Create New Site from GitHub

1. On Netlify dashboard, click **"Add new site"** → **"Import an existing project"**
2. Click **"Deploy with GitHub"**
3. **Grant Netlify access** to your repositories:
   - You'll see a GitHub authorization page
   - You can choose **"Only select repositories"** and pick your `ComplianceVault` repo
   - Or choose **"All repositories"** for easier access
4. Click **"Authorize Netlify"**

---

## Step 3: Configure Build Settings

1. **Select your repository**: Click on **`ComplianceVault`**
2. **Configure site settings**:

   | Setting | Value |
   |:--------|:------|
   | **Branch to deploy** | `main` |
   | **Base directory** | `frontend` |
   | **Build command** | *(leave empty)* |
   | **Publish directory** | `.` (or leave as default) |

3. Click **"Deploy site"**

Netlify will start building and deploying your site immediately!

---

## Step 4: Wait for Deployment

1. You'll see a deployment log screen
2. Wait for it to show: **"Site is live"** (usually takes 30-60 seconds)
3. Netlify will give you a temporary URL like:
   ```
   https://random-name-12345.netlify.app
   ```
4. **Click the URL** to test your site

---

## Step 5: Update API Connection

Your frontend needs to point to the Railway backend:

1. **Go back to your code editor**
2. Check `frontend/js/api.js` - it should already have:
   ```javascript
   const API_BASE = "https://compliancevault-production.up.railway.app/api";
   ```
3. If not, update it and push to GitHub

---

## Step 6: Configure Custom Domain (compliance.azbers.com)

### A. Add Domain in Netlify

1. In Netlify, go to your site → **"Domain settings"**
2. Click **"Add custom domain"**
3. Enter: `compliance.azbers.com`
4. Click **"Verify"**
5. Netlify will show: **"Check DNS Configuration"**

### B. Update DNS in GoDaddy

1. Log into **GoDaddy**
2. Go to **"My Products"** → **"DNS"** for `azbers.com`
3. Find your existing `compliance` CNAME record (or add a new one):
   - **Type**: CNAME
   - **Name**: `compliance`
   - **Value**: `random-name-12345.netlify.app` (use YOUR Netlify URL)
   - **TTL**: 600 seconds (or 1 hour)
4. **Save** the record

### C. Wait for DNS Propagation

1. DNS changes take 5-30 minutes to propagate
2. Go back to Netlify → **"Domain settings"**
3. Click **"Verify DNS configuration"**
4. Once verified, Netlify will automatically provision an **SSL certificate**

---

## Step 7: Enable HTTPS

1. After DNS is verified, go to **"Domain settings"** → **"HTTPS"**
2. Netlify automatically provisions a **free SSL certificate**
3. Enable **"Force HTTPS"** - this redirects all HTTP traffic to HTTPS

---

## Step 8: Update CORS on Railway

Your backend needs to allow requests from Netlify:

1. Go to **Railway Dashboard** → Your service → **"Variables"** tab
2. Find **`CORS_ORIGINS`** and update it to:
   ```
   https://compliance.azbers.com,https://random-name-12345.netlify.app,https://compliancevault-production.up.railway.app
   ```
   *(Replace with YOUR actual Netlify URL)*
3. **Save** - Railway will auto-redeploy

---

## Step 9: Disable GitHub Pages (Optional)

Since you're now using Netlify, you can disable GitHub Pages:

1. Go to GitHub → Your repo → **"Settings"** → **"Pages"**
2. Under **"Source"**, select **"None"**
3. **Save**

---

## Step 10: Make Repository Private

Now that Netlify is deploying from your private repo, secure your code:

1. Go to GitHub → Your repo → **"Settings"**
2. Scroll to **"Danger Zone"**
3. Click **"Change repository visibility"**
4. Select **"Make private"**
5. Type the repository name to confirm
6. Click **"I understand, change repository visibility"**

**Your code is now 100% private!** 🔒

---

## Step 11: Test Your Deployment

1. Visit: `https://compliance.azbers.com/`
2. Try to **register** a new account
3. Try to **login**
4. Upload an **evidence file**
5. Everything should work perfectly! ✅

---

## Auto-Deployment (Bonus Feature)

Every time you push code to GitHub, Netlify will **automatically rebuild and deploy** your frontend!

**To test this:**
1. Make a small change to `frontend/index.html` (e.g., change a title)
2. Commit and push to GitHub
3. Watch Netlify auto-deploy in real-time!

---

## Troubleshooting

### Site shows 404 or blank page
- **Check**: Base directory is set to `frontend`
- **Check**: Publish directory is `.` or empty
- Go to **"Site settings"** → **"Build & deploy"** to verify

### Backend not working / CORS errors
- **Check**: `CORS_ORIGINS` on Railway includes your Netlify URL
- **Check**: `frontend/js/api.js` points to the correct Railway URL
- Hard refresh your browser: `Ctrl + Shift + R`

### Custom domain not working
- **Check**: DNS record in GoDaddy points to `your-site.netlify.app` (not GitHub)
- **Wait**: DNS can take up to 30 minutes
- Verify DNS with: `https://dns.google/resolve?name=compliance.azbers.com&type=CNAME`

### SSL certificate pending
- **Wait**: SSL provisioning takes 5-10 minutes after DNS is verified
- **Check**: DNS is correctly configured in GoDaddy

---

## 🎉 Success!

Your ComplianceVault platform is now:
- ✅ Deployed on **Netlify** (frontend)
- ✅ Backend on **Railway**
- ✅ Custom domain: `https://compliance.azbers.com/`
- ✅ **Repository is PRIVATE and secure**
- ✅ Automatic deployments on every push
- ✅ Free SSL/HTTPS on both frontend and backend

**Your professional compliance platform is now live and secure!** 🚀
