# 🚀 RIZZK Calculator - Manual Azure Deployment Guide

## ⚠️ Azure CLI Installation Failed Due to Disk Space

Since Azure CLI can't be installed due to disk space constraints, we'll deploy manually through the Azure Portal.

## 📋 Step-by-Step Manual Deployment

### Step 1: Create Azure Web App

1. **Open Azure Portal**: Go to https://portal.azure.com
2. **Sign in** with your Microsoft account (you're already signed in)
3. **Create Resource**:
   - Click **"Create a resource"** (top left)
   - Search for **"Web App"**
   - Click **"Create"** → **"Web App"**

4. **Configure Web App**:
   - **Subscription**: Your subscription
   - **Resource Group**: Click **"Create new"** → Name: `rizzk-calculator-rg`
   - **Name**: `rizzk-calculator-demo` (must be globally unique)
   - **Publish**: **Code**
   - **Runtime stack**: **Python 3.11**
   - **Operating System**: **Linux**
   - **Region**: **East US** (or closest to you)
   - **App Service Plan**:
     - Click **"Create new"**
     - Name: `rizzk-calculator-plan`
     - Pricing tier: **B1 (Basic)** - $13/month (recommended) or **F1 (Free)**

5. **Review & Create**:
   - Click **"Review + create"**
   - Click **"Create"**
   - Wait 2-3 minutes for deployment

### Step 2: Configure Application Settings

1. **Navigate to your Web App**:
   - Go to **"Go to resource"** or search for `rizzk-calculator-demo` in portal

2. **Configure Settings**:
   - In your Web App, go to **"Configuration"** (under Settings)
   - Click **"Application settings"** tab
   - Click **"+ New application setting"** for each:

     | Name | Value | Notes |
     |------|-------|-------|
     | `WEBSITES_PORT` | `8501` | Required for Streamlit |
     | `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | Enables pip install |
     | `EDGY_MODE_DEFAULT` | `false` | UI mode default |

   - Click **"Save"** (top of page)

3. **Set Startup Command**:
   - In **"General settings"** tab:
   - **Startup Command**: `bash startup.sh`
   - Click **"Save"**

### Step 3: Deploy Your Code

**Option A: Deploy from GitHub (Recommended)**

1. In your Web App, go to **"Deployment Center"** (under Deployment)
2. **Source**: **GitHub**
3. **Sign in to GitHub** and authorize Azure
4. **Organization**: `fuaadabdullah`
5. **Repository**: `rr-calculator`
6. **Branch**: `manual-pr-branch`
7. **Build provider**: **GitHub Actions**
8. Click **"Save"**
9. Wait for deployment (5-10 minutes)

**Option B: Manual Upload via FTP**

1. In **"Deployment Center"**, note the FTP credentials
2. Use an FTP client (like FileZilla) or VS Code FTP extension
3. Upload all files from:
   ```
   /Users/fuaadabdullah/ForgeMonorepo/Fuaad's Portfolio/RIZZK-Calculator-Demo/risk_reward_calculator/
   ```
4. To the FTP root directory

### Step 4: Enable Logging (Optional but Recommended)

1. In your Web App, go to **"App Service logs"** (under Monitoring)
2. **Application Logging**: **File System**
3. **Level**: **Information**
4. **Web server logging**: **File System**
5. Click **"Save"**

### Step 5: Test Your Deployment

1. In your Web App overview, click the **URL** at the top:
   ```
   https://rizzk-calculator-demo.azurewebsites.net
   ```

2. **Expected Result**: Your RIZZK Calculator should load with:
   - 🦇 Header with bat emoji
   - Form with position type, risk mode, account size, etc.
   - Light gray background around the form
   - All calculations working

### Step 6: Troubleshooting

**If app shows "Application Error"**:
- Check **"Log stream"** in Azure Portal (under Monitoring)
- Look for Python import errors or startup issues
- Verify `WEBSITES_PORT=8501` is set
- Restart the app: Click **"Restart"** in overview

**If form doesn't load**:
- Check browser console for errors
- Verify all files were uploaded (use Kudu console)
- Test locally: `streamlit run app.py --server.port=8501`

**If dependencies fail**:
- Check `requirements.txt` is uploaded
- Verify Python 3.11 runtime is selected

---

## 📊 Cost Estimate

- **Free Tier (F1)**: $0/month, 60 CPU minutes/day
- **Basic Tier (B1)**: ~$13/month, always-on, 1.75 GB RAM

---

## 🆘 Need Help?

1. **Check logs**: Azure Portal → Your App → Log stream
2. **File verification**: Use Kudu console at `https://rizzk-calculator-demo.scm.azurewebsites.net`
3. **Restart app**: Azure Portal → Your App → Restart

---

## ✅ Success Checklist

- [ ] Web App created in Azure Portal
- [ ] Application settings configured (WEBSITES_PORT=8501, etc.)
- [ ] Startup command set to `bash startup.sh`
- [ ] Code deployed from GitHub or FTP
- [ ] App accessible at the URL
- [ ] Form loads with light gray background
- [ ] Calculations work correctly

---

**Your app will be live at: https://rizzk-calculator-demo.azurewebsites.net**

Let me know if you encounter any issues during deployment!