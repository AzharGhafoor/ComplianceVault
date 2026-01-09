## Step 0: Uploading to GitHub

Before deploying, you need to push your code to a new GitHub repository.

1.  **Create a New Repository** on GitHub.com (keep it Public or Private).
2.  **Open PowerShell** in the project directory (`niap-compliance-platform`).
3.  **Run these commands**:
    ```powershell
    # Initialize the repository
    git init
    
    # Add all files (it will ignore files listed in .gitignore)
    git add .
    
    # Create your first commit
    git commit -m "Initial commit for NIAP platform"
    
    # Link to your GitHub repo (USE THE HTTPS URL HERE)
    # Example: https://github.com/azhar/niap-compliance.git
    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
    
    # If you get a "Public Key" error, run this to fix it:
    # git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

    # Push the code
    git branch -M main
    git push -u origin main
    ```

> [!TIP]
> **Authentication**: When you push, a window might pop up asking you to log in. Log in using your browser or a Personal Access Token (PAT).

---

## Step 1: Backend Deployment (Render.com)

On the **"Create a New Web Service"** page, use these exact settings:

1.  **Name**: `compliance-vault-api` (or any name you like)
2.  **Language**: `Python 3`
3.  **Branch**: `main`
4.  **Region**: `Oregon (US West)` (Default is fine)
5.  **Root Directory**: (Leave Empty)
6.  **Build Command**: `pip install -r requirements.txt`
7.  **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
8.  **Instance Type**: `Free`

### 🔑 Critical: Environment Variables
Scroll down to the **Environment Variables** section and add these three:

| Key | Value |
| :--- | :--- |
| `DATABASE_URL` | `sqlite:///./compliance_vault.db` |
| `SECRET_KEY` | `EnterARandomLongStringOfLettersAndNumbers` |
| `DEBUG` | `False` |

*Click **Create Web Service** at the bottom.*

---

## Alternative: Hosting on Koyeb (No Credit Card required)

If Render asks for a credit card, **Koyeb.com** is a great alternative that often lets you start without one.

1.  **Sign up** at [Koyeb.com](https://www.koyeb.com).
2.  **Create Service**: Select "GitHub" and connect your repo.
3.  **App Category**: Web Service.
4.  **Instance**: Free (Nano).
5.  **Build/Run Commands**:
    -   **Build Command**: Leave **EMPTY** (Turn off the "Override" toggle).
    -   **Run Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (Turn ON "Override").
6.  **Env Vars**: Add `DATABASE_URL`, `SECRET_KEY`, and `DEBUG` just like in Render.

## Option 3: Hosting on Railway.app (Trial/Credits)

Railway is very fast and efficient, but it uses a **$5 Trial Credit** system.

1.  **Sign up**: Go to [Railway.app](https://railway.app) and login with GitHub.
2.  **New Project**: Select "Deploy from GitHub repo".
3.  **🔧 IMPORTANT: Set up Data Persistence (SQLite)**:
    -   Once deployed, go to your service dashboard.
    -   Click the **"Settings"** tab.
    -   Find **"Volumes"** and click **"Add Volume"**.
    -   Set **Mount Path** to: `/data`.
4.  **🔑 Update Env Vars**:
    -   Go to the **"Variables"** tab.
    -   Set `DATABASE_URL` to: `sqlite:////data/compliance_vault.db`
    -   Add `SECRET_KEY` and `DEBUG=False`.
5.  **Restart**: Redeploy or Restart the service to apply the volume.

---

## Step 2: Frontend Deployment (GitHub Pages)

Once Render gives you a URL (e.g., `https://compliance-vault-api.onrender.com`), do this:

1.  **Update API URL**:
    -   Open `frontend/js/api.js`.
    -   Change the `BASE_URL`:
        ```javascript
        const BASE_URL = 'https://compliance-vault-api.onrender.com/api';
        ```
2.  **Push to GitHub**:
    ```powershell
    git add frontend/js/api.js
    git commit -m "Update API URL for production"
    git push origin main
    ```
3.  **Enable GitHub Pages**:
    -   Go to Repo **Settings** -> **Pages**.
    -   **Source**: Deploy from a branch.
    -   **Branch**: `main` / **Folder**: `/ (root)`.

## Step 3: Domain Mapping (GoDaddy & azbers.com)

To use your own domain, we will use **Subdomains** to keep the frontend and backend separate but under your brand.

### Recommended Setup:
-   **Frontend (The website)**: `compliance.azbers.com`
-   **Backend (The data server)**: `api.azbers.com`

### 1. Configure GoDaddy DNS
Log into GoDaddy, go to **DNS Management** for `azbers.com`, and add these records:

| Type | Name | Value | Purpose |
| :--- | :--- | :--- | :--- |
| **CNAME** | `compliance` | `[your-username].github.io` | Points to your GitHub site |
| **CNAME** | `api` | `[your-app-name].onrender.com` | Points to your data server |

### 2. Update Render (Backend)
-   Go to your Render Dashboard -> **Settings** -> **Custom Domains**.
-   Add `api.azbers.com`. Render will issue an SSL (HTTPS) certificate automatically.

### 3. Update GitHub (Frontend)
-   In your GitHub repo -> **Settings** -> **Pages**.
-   Under **Custom Domain**, enter `compliance.azbers.com`.
-   **CRITICAL**: Check "Enforce HTTPS".

---

## Step 4: Final Connection (The Glue)

Once your domains are set, you must tell the frontend where the backend is:

1.  Open `frontend/js/api.js`.
2.  Change the `BASE_URL` to your new domain:
    ```javascript
    const BASE_URL = 'https://api.azbers.com/api';
    ```
3.  Push this change to GitHub.

---

## Step 5: Database Cleanup (Final Reset)
- [ ] Change `SECRET_KEY` in `.env`.
- [ ] Set `DEBUG=False` in production.
- [ ] Update `CORS_ORIGINS` with the production URL.
- [ ] Test the login with the default admin account: `admin@compliancevault.pro` / `Admin123!`.
