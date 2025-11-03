#!/bin/bash

# RIZZK Calculator - Azure Deployment Quick Start
# This script helps you deploy to Azure App Service

echo "🦇 RIZZK Calculator - Azure Deployment Helper"
echo "=============================================="
echo ""

# Check if logged into Azure
echo "Step 1: Checking Azure login status..."
if command -v az &> /dev/null; then
    az account show &> /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ You are logged into Azure"
        SUBSCRIPTION=$(az account show --query name -o tsv)
        echo "   Subscription: $SUBSCRIPTION"
    else
        echo "❌ Not logged into Azure. Please run: az login"
        exit 1
    fi
else
    echo "⚠️  Azure CLI not installed"
    echo "   Please use VS Code Azure App Service extension for deployment"
    echo "   See AZURE_DEPLOYMENT.md for instructions"
    exit 0
fi

echo ""
echo "Step 2: Setting deployment variables..."
APP_NAME="rizzk-calculator-${USER}"
RESOURCE_GROUP="rizzk-calculator-rg"
LOCATION="eastus"
PLAN_NAME="rizzk-calculator-plan"
RUNTIME="PYTHON:3.11"
SKU="B1"

echo "   App Name: $APP_NAME"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Location: $LOCATION"
echo "   Runtime: $RUNTIME"
echo "   SKU: $SKU"
echo ""

read -p "Do you want to proceed with deployment? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "Step 3: Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION
if [ $? -ne 0 ]; then
    echo "❌ Failed to create resource group"
    exit 1
fi
echo "✅ Resource group created"

echo ""
echo "Step 4: Creating App Service plan..."
az appservice plan create \
  --name $PLAN_NAME \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku $SKU
if [ $? -ne 0 ]; then
    echo "❌ Failed to create App Service plan"
    exit 1
fi
echo "✅ App Service plan created"

echo ""
echo "Step 5: Creating Web App..."
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $PLAN_NAME \
  --name $APP_NAME \
  --runtime "$RUNTIME"
if [ $? -ne 0 ]; then
    echo "❌ Failed to create Web App"
    exit 1
fi
echo "✅ Web App created"

echo ""
echo "Step 6: Configuring startup command..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --startup-file "bash startup.sh"
if [ $? -ne 0 ]; then
    echo "❌ Failed to set startup command"
    exit 1
fi
echo "✅ Startup command configured"

echo ""
echo "Step 7: Setting application settings..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    WEBSITES_PORT=8501 \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    EDGY_MODE_DEFAULT=false
if [ $? -ne 0 ]; then
    echo "❌ Failed to set application settings"
    exit 1
fi
echo "✅ Application settings configured"

echo ""
echo "Step 8: Deploying application code..."
az webapp up \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --runtime "$RUNTIME" \
  --sku $SKU
if [ $? -ne 0 ]; then
    echo "❌ Deployment failed"
    exit 1
fi
echo "✅ Application deployed"

echo ""
echo "Step 9: Enabling logging..."
az webapp log config \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --application-logging filesystem \
  --level information \
  --web-server-logging filesystem
if [ $? -ne 0 ]; then
    echo "⚠️  Failed to enable logging (non-critical)"
fi

echo ""
echo "=============================================="
echo "🎉 Deployment Complete!"
echo "=============================================="
echo ""
echo "Your app is now available at:"
echo "https://${APP_NAME}.azurewebsites.net"
echo ""
echo "Next steps:"
echo "1. Visit the URL above to verify deployment"
echo "2. Check logs: az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME"
echo "3. View in Azure Portal: https://portal.azure.com"
echo ""
echo "Resource details:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  App Service Plan: $PLAN_NAME"
echo "  Web App: $APP_NAME"
echo ""
echo "To delete all resources later:"
echo "  az group delete --name $RESOURCE_GROUP --yes --no-wait"
echo ""
