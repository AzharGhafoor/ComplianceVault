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

1.  **Create a Render Account**: Go to [render.com](https://render.com).
2.  **New Web Service**: Connect your GitHub repository.
3.  **Configure**:
    -   **Runtime**: `Python`
    -   **Build Command**: `pip install -r requirements.txt`
    -   **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4.  **Persistent Storage** (Optional but Recommended):
    -   SQLite files get deleted every time Render restarts on the free tier.
    -   To keep data, go to **Disk** -> **Add Disk** and mount it at `/data`.
    -   Update your `.env` to `DATABASE_URL=sqlite:////data/compliance_vault.db`.
5.  **Environment Variables**:
    -   Add `SECRET_KEY` (a random long string).
    -   Add `CORS_ORIGINS` (include your future `.github.io` URL).

---

## Step 2: Frontend Deployment (GitHub Pages)

1.  **Update API URL**:
    -   In `frontend/js/api.js`, change the `BASE_URL` to your Render app URL (e.g., `https://niap-backend.onrender.com/api`).
2.  **Push to GitHub**:
    -   Ensure your `frontend/` folder is in the root or appropriate subfolder.
3.  **Enable GitHub Pages**:
    -   Go to Repository **Settings** -> **Pages**.
    -   Select the branch and the `/frontend` folder (if you move it to a dedicated branch or folder).
    -   *Preferred*: Use a dedicated `gh-pages` branch containing only the contents of the `frontend/` directory.

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
