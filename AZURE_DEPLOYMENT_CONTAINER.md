---
description: "AZURE_DEPLOYMENT_CONTAINER"
---

# Azure Deployment (Web App for Containers)

This guide deploys the Streamlit app as a Linux container from Docker Hub.

## Prerequisites
- Docker image pushed to Docker Hub: `fuaadabdullah/rizzk-calculator:latest`
- Azure subscription (Azure for Students). If region policy blocks some regions, use `East US`.

## One-command deploy (recommended: Azure Cloud Shell)

1. Open https://portal.azure.com → Cloud Shell (Bash)
2. Upload this repo folder or copy/paste the script content
3. Run:

```bash
bash deploy_container_to_azure.sh rizzk-calculator-demo-eus
```

- If the app name is taken, use a different globally unique name.
- The script creates:
  - Resource Group: `rizzk-rg-eus`
  - App Service Plan: `rizzk-plan-eus` (Linux, `B1`)
  - Web App: your chosen name, region `East US`
  - Container image: `fuaadabdullah/rizzk-calculator:latest`
  - App settings: `WEBSITES_PORT=8501`, `EDGY_MODE_DEFAULT=false`

## Manual portal setup (alternative)

- Create → Web App → Basics
  - Subscription: Azure for Students
  - Resource Group: `rizzk-rg-eus` (or create new)
  - Name: `rizzk-calculator-demo-eus` (unique)
  - Publish: Container
  - Operating System: Linux
  - Region: East US
  - Plan: B1 (Basic)
- Container tab
  - Sidecar support: Disabled
  - Image Source: Other container registries
  - Docker hub options → Access Type: Public
  - Registry server URL: (leave blank)
  - Image and tag: `fuaadabdullah/rizzk-calculator:latest`
  - Port: `8501`
  - Startup Command: (leave blank — Dockerfile CMD handles it)
- After creation → Configuration → Application settings
  - `WEBSITES_PORT = 8501`
  - `EDGY_MODE_DEFAULT = false`
  - Save → Restart

## Verify
- Open: `https://<your-app-name>.azurewebsites.net`
- If 502 initially, wait 1–2 minutes for image pull.
- Logs: Web App → Log stream. You should see `Streamlit ... running at http://0.0.0.0:8501`.

## Update flow
- Rebuild and push image:

```bash
docker build -t fuaadabdullah/rizzk-calculator:latest .
docker push fuaadabdullah/rizzk-calculator:latest
```

- Restart the Web App to pull latest image:

```bash
az webapp restart -g rizzk-rg-eus -n rizzk-calculator-demo-eus
```

