# 🚀 Deploy to Azure Container Instances

## Prerequisites
- Azure CLI installed
- Docker installed
- Azure account with Container Registry

## Step 1: Install Azure CLI
```bash
# macOS
brew install azure-cli

# Ubuntu/Debian
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Windows
# Download from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows
```

## Step 2: Login to Azure
```bash
az login
```

## Step 3: Create Resource Group
```bash
az group create --name emergency-support-rg --location eastus
```

## Step 4: Create Container Registry
```bash
# Create ACR
az acr create --resource-group emergency-support-rg --name yourregistry --sku Basic

# Login to ACR
az acr login --name yourregistry
```

## Step 5: Build and Push Images
```bash
# Build backend image
docker build -t yourregistry.azurecr.io/backend:latest ./backend
docker push yourregistry.azurecr.io/backend:latest

# Build client-r image
docker build -t yourregistry.azurecr.io/client-r:latest ./client_r
docker push yourregistry.azurecr.io/client-r:latest

# Build consumer-app image
docker build -t yourregistry.azurecr.io/consumer-app:latest ./consumer-app
docker push yourregistry.azurecr.io/consumer-app:latest

# Build legal-entity-consumer-app image
docker build -t yourregistry.azurecr.io/legal-entity-consumer-app:latest ./legal-entity-consumer-app
docker push yourregistry.azurecr.io/legal-entity-consumer-app:latest
```

## Step 6: Deploy to Container Instances
```bash
# Deploy backend
az container create \
  --resource-group emergency-support-rg \
  --name backend \
  --image yourregistry.azurecr.io/backend:latest \
  --dns-name-label emergency-backend \
  --ports 5000 \
  --environment-variables DATABASE_URI=sqlite:///emergency_support.db OPENAI_MODEL=gpt-4o-mini

# Deploy client-r
az container create \
  --resource-group emergency-support-rg \
  --name client-r \
  --image yourregistry.azurecr.io/client-r:latest \
  --dns-name-label emergency-client-r \
  --ports 3000 \
  --environment-variables REACT_APP_MAPBOX_TOKEN=pk.eyJ1IjoidnA0NTEiLCJhIjoiY21nYjltdXB5MHdkYjJqczdkdzdoMzJsbiJ9.7nq6toK2LmmlYx2wZupdVg

# Deploy consumer-app
az container create \
  --resource-group emergency-support-rg \
  --name consumer-app \
  --image yourregistry.azurecr.io/consumer-app:latest \
  --dns-name-label emergency-consumer \
  --ports 4173 \
  --environment-variables VITE_API_URL=http://emergency-backend.eastus.azurecontainer.io:5000

# Deploy legal-entity-consumer-app
az container create \
  --resource-group emergency-support-rg \
  --name legal-entity-consumer-app \
  --image yourregistry.azurecr.io/legal-entity-consumer-app:latest \
  --dns-name-label emergency-legal \
  --ports 4173 \
  --environment-variables VITE_API_URL=http://emergency-backend.eastus.azurecontainer.io:5000
```

## Step 7: Check Deployment Status
```bash
# List containers
az container list --resource-group emergency-support-rg --output table

# Check logs
az container logs --resource-group emergency-support-rg --name backend
az container logs --resource-group emergency-support-rg --name client-r
```

## Step 8: Access Your Applications
```bash
# Get FQDN for each service
az container show --resource-group emergency-support-rg --name backend --query ipAddress.fqdn
az container show --resource-group emergency-support-rg --name client-r --query ipAddress.fqdn
az container show --resource-group emergency-support-rg --name consumer-app --query ipAddress.fqdn
az container show --resource-group emergency-support-rg --name legal-entity-consumer-app --query ipAddress.fqdn
```

## Alternative: Deploy with YAML
```bash
# Deploy using the YAML file
az container create --resource-group emergency-support-rg --file azure-deploy.yml
```

## Important Notes:
- Each container gets its own public IP and FQDN
- Update VITE_API_URL to point to the backend's FQDN
- Consider using Azure Container Apps for better orchestration
- Monitor costs as each container instance is billed separately
- Use Azure Key Vault for sensitive environment variables
