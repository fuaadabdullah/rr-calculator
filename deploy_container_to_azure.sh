#!/usr/bin/env bash
set -euo pipefail

# Deploy RIZZK Calculator as a Linux Web App for Containers (Docker Hub public image)
# Recommended to run in Azure Cloud Shell (no local installs required).
#
# Usage:
#   ./deploy_container_to_azure.sh [--name|-n APP_NAME] [--image|-i REPO[:TAG]] [--tag|-t TAG] [--force-refresh|-f] [APP_NAME]
#
# Notes:
# - APP_NAME can be provided either as --name or as a final positional arg (kept for backward compatibility).
# - You can override the image via:
#     env IMAGE=repo[:tag] ./deploy_container_to_azure.sh
#     or flags: --image repo[:tag] and/or --tag tag
# - --force-refresh toggles a harmless app setting to ensure a pull even when reusing the same tag (e.g., :latest).

APP_NAME_DEFAULT="rizzk-calculator-demo-eus2-f1"
RESOURCE_GROUP="rizzk-rg-wus2"
LOCATION="eastus2"
PLAN_NAME="rizzk-plan-eus2-f1"
SKU="F1"

# Image controls
DEFAULT_IMAGE_REPO="fuaadabdullah/rizzk-calculator"  # public Docker Hub repo
DEFAULT_IMAGE_TAG="latest"

# Flags (defaults)
APP_NAME="$APP_NAME_DEFAULT"
FORCE_REFRESH="false"
IMAGE_FROM_ENV="${IMAGE:-}"  # optional full image from env var
IMAGE_FLAG=""                 # optional full image from --image
TAG_FLAG=""                   # optional tag from --tag

usage() {
  cat <<EOF
Usage: $0 [options] [APP_NAME]

Options:
  -n, --name APP_NAME     Web App name (globally unique). Default: ${APP_NAME_DEFAULT}
  -i, --image REPO[:TAG]  Full container image (e.g., repo/name:tag). Overrides defaults.
  -t, --tag TAG           Image tag to use (e.g., v0.2.0). If used with --image, replaces its tag.
  -f, --force-refresh     Toggle a harmless app setting to bust cache and re-pull image.
  -h, --help              Show this help and exit.

Env overrides:
  IMAGE=repo[:tag]        Same as --image; can be combined with --tag to replace tag.
EOF
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--name)
      APP_NAME="$2"; shift 2;;
    -i|--image)
      IMAGE_FLAG="$2"; shift 2;;
    -t|--tag)
      TAG_FLAG="$2"; shift 2;;
    -f|--force-refresh)
      FORCE_REFRESH="true"; shift;;
    -h|--help)
      usage; exit 0;;
    --) shift; break;;
    -*)
      echo "Unknown option: $1" >&2
      usage; exit 2;;
    *)
      # positional APP_NAME (kept for backward compatibility)
      APP_NAME="$1"; shift;;
  esac
done

say() { echo -e "\n(⌐■_■) $*\n"; }

# Check Azure CLI availability
if ! command -v az >/dev/null 2>&1; then
  say "Azure CLI (az) not found. Recommended: run in Azure Cloud Shell (portal.azure.com > Cloud Shell).\nIf running locally, install Azure CLI: https://learn.microsoft.com/cli/azure/install-azure-cli"
  exit 1
fi

# Determine final image value
RESOLVED_IMAGE=""
if [[ -n "$IMAGE_FLAG" ]]; then
  RESOLVED_IMAGE="$IMAGE_FLAG"
elif [[ -n "$IMAGE_FROM_ENV" ]]; then
  RESOLVED_IMAGE="$IMAGE_FROM_ENV"
else
  RESOLVED_IMAGE="${DEFAULT_IMAGE_REPO}:${DEFAULT_IMAGE_TAG}"
fi

# If a tag was provided, ensure it overrides/sets the tag on the resolved image
if [[ -n "$TAG_FLAG" ]]; then
  if [[ "$RESOLVED_IMAGE" == *:* ]]; then
    RESOLVED_IMAGE="${RESOLVED_IMAGE%:*}:$TAG_FLAG"
  else
    RESOLVED_IMAGE="${RESOLVED_IMAGE}:$TAG_FLAG"
  fi
fi

IMAGE="$RESOLVED_IMAGE"

# Ensure logged in
if ! az account show >/dev/null 2>&1; then
  say "Logging into Azure..."
  az login
fi

say "Using subscription: $(az account show --query name -o tsv)"
say "Target Web App: $APP_NAME"
say "Container Image: $IMAGE"

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
    --container-image-name "$IMAGE" \
    --output table || true
fi

# Required App Settings
WEBSITES_PORT="8501"
EDGY_MODE_DEFAULT="false"

SETTINGS=("WEBSITES_PORT=$WEBSITES_PORT" "EDGY_MODE_DEFAULT=$EDGY_MODE_DEFAULT")
if [[ "$FORCE_REFRESH" == "true" ]]; then
  BUSTER="$(date +%s)"
  SETTINGS+=("FORCE_REFRESH=$BUSTER")
  say "Force refresh enabled; applying cache-buster app setting: FORCE_REFRESH=$BUSTER"
fi

say "Applying App Settings ($(IFS=, ; echo "${SETTINGS[*]}") )"
az webapp config appsettings set \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --settings "${SETTINGS[@]}" \
  --output table

say "Restarting Web App"
az webapp restart \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --output none

say "Deployment complete. Browse: https://$APP_NAME.azurewebsites.net"
