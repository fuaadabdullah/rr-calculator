# Azure App Service Deployment Guide for RIZZK Calculator

## Prerequisites ✅
- [x] Azure App Service extension installed in VS Code
- [x] Signed into Microsoft/Azure account
- [x] `startup.sh` created
- [x] `.deployment` file created
- [x] All dependencies in `requirements.txt`

## Method 1: Deploy via VS Code (Recommended)

### Step 1: Open Azure Extension
1. Click the **Azure icon** in the VS Code sidebar (left side)
2. You should see "RESOURCES" section with your subscription

### Step 2: Create Web App
1. In the Azure panel, expand your subscription
2. Right-click on **"App Services"** → **"Create New Web App... (Advanced)"**
3. Enter the following details when prompted:

   **App Name**: `rizzk-calculator-demo` (must be globally unique)
   
   **Resource Group**: 
   - Select "Create new resource group"
   - Name: `rizzk-calculator-rg`
   
   **Runtime Stack**: `Python 3.11`
   
   **Operating System**: `Linux`
   
   **Region**: `East US` (or your preferred region)
   
   **App Service Plan**:
   - Select "Create new App Service plan"
   - Name: `rizzk-calculator-plan`
   - Pricing tier: `B1` (Basic - recommended) or `F1` (Free)
   
   **Application Insights**: Skip for now (select "Skip for now")

### Step 3: Deploy the Application
1. After the Web App is created, right-click on the **project folder** in VS Code Explorer:
   ```
   /Users/fuaadabdullah/ForgeMonorepo/Fuaad's Portfolio/RIZZK-Calculator-Demo/risk_reward_calculator
   ```
2. Select **"Deploy to Web App..."**
3. Choose the Web App you just created: `rizzk-calculator-demo`
4. Confirm the deployment when prompted
5. Wait for deployment to complete (2-5 minutes)

### Step 4: Configure Application Settings
1. In Azure panel, find your Web App under "App Services"
2. Right-click → **"Open in Portal"**
3. In Azure Portal:
   - Go to **"Configuration"** (under Settings)
   - Click **"Application settings"** tab
   - Click **"+ New application setting"** and add:
     
     | Name | Value |
     |------|-------|
     | `WEBSITES_PORT` | `8501` |
     | `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |
     | `EDGY_MODE_DEFAULT` | `false` |
   
   - Click **"Save"** at the top

4. Go to **"General settings"** tab:
   - **Startup Command**: `bash startup.sh`
   - Click **"Save"**

### Step 5: Restart the App
1. In Azure panel (VS Code), right-click your Web App
2. Select **"Restart"**
3. Wait 30 seconds

### Step 6: View Your App
1. Right-click your Web App in Azure panel
2. Select **"Browse Website"**
3. Your app will open at: `https://rizzk-calculator-demo.azurewebsites.net`

---

## Method 2: Deploy via Azure Portal (Manual Upload)

### If VS Code deployment doesn't work:

1. **Create Web App in Azure Portal**:
   - Go to https://portal.azure.com
   - Click **"Create a resource"** → **"Web App"**
   - Fill in the same details as Method 1
   - Click **"Review + Create"** → **"Create"**

2. **Upload Files via FTP or Kudu**:
   - In your Web App, go to **"Deployment Center"**
   - Note the FTP credentials or use Kudu
   - Upload all files from `risk_reward_calculator` folder

3. **Configure as in Method 1, Step 4**

---

## Method 3: Deploy via Azure CLI (When Azure CLI is available)

If you install Azure CLI later, run these commands:

```bash
# Login to Azure
az login

# Set variables
APP_NAME="rizzk-calculator-demo"
RESOURCE_GROUP="rizzk-calculator-rg"
LOCATION="eastus"
PLAN_NAME="rizzk-calculator-plan"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create App Service plan
az appservice plan create \
  --name $PLAN_NAME \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1

# Create web app
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $PLAN_NAME \
  --name $APP_NAME \
  --runtime "PYTHON:3.11"

# Configure startup command
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --startup-file "bash startup.sh"

# Set app settings
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    WEBSITES_PORT=8501 \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    EDGY_MODE_DEFAULT=false

# Deploy from local directory
cd "/Users/fuaadabdullah/ForgeMonorepo/Fuaad's Portfolio/RIZZK-Calculator-Demo/risk_reward_calculator"
az webapp up \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --runtime PYTHON:3.11
```

---

## Troubleshooting

### View Logs
1. In Azure panel, right-click your Web App → **"Open in Portal"**
2. Go to **"Log stream"** (under Monitoring)
3. Watch for startup errors

### Common Issues

**Issue**: App shows "Application Error"
- **Solution**: Check startup command is set to `bash startup.sh`
- Ensure `WEBSITES_PORT` is set to `8501`

**Issue**: App not loading
- **Solution**: Restart the app and wait 1-2 minutes
- Check logs for Python errors

**Issue**: Missing dependencies
- **Solution**: Ensure `requirements.txt` includes all packages
- Redeploy the app

**Issue**: Import errors for `rizzk_core`
- **Solution**: Verify `rizzk_core.py` is in the same directory as `app.py`

### Enable Detailed Logging
1. Go to **"App Service logs"** in Azure Portal
2. Enable **"Application Logging (Filesystem)"** → Level: **"Information"**
3. Enable **"Web server logging"** → **"File System"**
4. Click **"Save"**

---

## Expected Result

Your app should be live at:
```
https://rizzk-calculator-demo.azurewebsites.net
```

Features:
- ✅ Streamlit RIZZK Calculator UI
- ✅ Position size calculations
- ✅ Risk/Reward charts
- ✅ History tracking
- ✅ Responsive design

---

## Cost Estimate

**Free Tier (F1)**:
- Cost: $0/month
- Limited: 60 CPU minutes/day, 1 GB RAM

**Basic Tier (B1)**:
- Cost: ~$13/month
- Better: Always-on, 1.75 GB RAM, custom domain support

---

## Next Steps After Deployment

1. **Test the app** thoroughly
2. **Set up custom domain** (optional)
3. **Enable HTTPS** (automatic with Azure)
4. **Monitor performance** in Azure portal
5. **Set up CI/CD** for automatic deployments from GitHub

---

## Support

If deployment fails, check:
1. Azure Activity Log in portal
2. Log Stream for runtime errors
3. Kudu Console for file verification: `https://<app-name>.scm.azurewebsites.net`
