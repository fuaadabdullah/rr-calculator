#!/usr/bin/env bash
set -euo pipefail

# Deploy RIZZK Calculator as a Linux Web App for Containers (Docker Hub public image)
# Recommended to run in Azure Cloud Shell (no local installs required).
# Usage: ./deploy_container_to_azure.sh [optional-app-name]
#   app name must be globally unique; defaults to rizzk-calculator-demo-eus

APP_NAME_DEFAULT="rizzk-calculator-demo-eus"
APP_NAME="${1:-$APP_NAME_DEFAULT}"
RESOURCE_GROUP="rizzk-rg-eus"
LOCATION="eastus"
PLAN_NAME="rizzk-plan-eus"
SKU="B1"
IMAGE="fuaadabdullah/rizzk-calculator:latest"  # public Docker Hub image

# Required App Settings
WEBSITES_PORT="8501"
EDGY_MODE_DEFAULT="false"

say() { echo -e "\n🦇 $*\n"; }

# Check Azure CLI availability
if ! command -v az >/dev/null 2>&1; then
  say "Azure CLI not found. Run this in Azure Cloud Shell (portal.azure.com > Cloud Shell) or install az locally."
  exit 1
fi

# Ensure logged in
if ! az account show >/dev/null 2>&1; then
  say "Logging into Azure..."
  az login
fi

say "Using subscription: $(az account show --query name -o tsv)"

say "Creating/Updating Resource Group: $RESOURCE_GROUP in $LOCATION"
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output table

say "Creating/Updating App Service Plan: $PLAN_NAME ($SKU, Linux)"
az appservice plan create \
  --name "$PLAN_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --sku "$SKU" \
  --is-linux \
  --location "$LOCATION" \
  --output table || true

# Create the Web App (container). If it exists, skip creation.
if ! az webapp show -g "$RESOURCE_GROUP" -n "$APP_NAME" >/dev/null 2>&1; then
  say "Creating Web App: $APP_NAME (Container)"
  az webapp create \
    --resource-group "$RESOURCE_GROUP" \
    --plan "$PLAN_NAME" \
    --name "$APP_NAME" \
    --deployment-container-image-name "$IMAGE" \
    --output table
else
  say "Web App $APP_NAME already exists; updating container config"
  az webapp config container set \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --docker-custom-image-name "$IMAGE" \
    --output table || true
fi

say "Applying App Settings (WEBSITES_PORT=$WEBSITES_PORT, EDGY_MODE_DEFAULT=$EDGY_MODE_DEFAULT)"
az webapp config appsettings set \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --settings WEBSITES_PORT="$WEBSITES_PORT" EDGY_MODE_DEFAULT="$EDGY_MODE_DEFAULT" \
  --output table

say "Restarting Web App"
az webapp restart \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --output none

say "Deployment complete. Browse: https://$APP_NAME.azurewebsites.net"
