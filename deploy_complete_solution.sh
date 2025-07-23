#!/bin/bash
# Complete Deployment Script for Azure Web App tf-ai-aivoice-dev-api-68s3
# This script handles the complete deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse command line arguments
SKIP_TERRAFORM=false
SKIP_GITHUB=false
VALIDATE_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-terraform)
            SKIP_TERRAFORM=true
            shift
            ;;
        --skip-github)
            SKIP_GITHUB=true
            shift
            ;;
        --validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}🚀 Azure Web App Deployment Script${NC}"
echo -e "${GREEN}=================================${NC}"
echo -e "${CYAN}Web App: tf-ai-aivoice-dev-api-68s3${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run command with error handling
run_command() {
    local cmd="$1"
    local description="$2"
    
    echo -e "${YELLOW}⏳ $description...${NC}"
    if eval "$cmd"; then
        echo -e "${GREEN}✅ $description completed successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ $description failed${NC}"
        return 1
    fi
}

# Check prerequisites
echo -e "${BLUE}🔍 Checking Prerequisites...${NC}"
prereqs_ok=true

if ! command_exists terraform; then
    echo -e "${RED}❌ Terraform not found. Please install Terraform CLI${NC}"
    prereqs_ok=false
else
    echo -e "${GREEN}✅ Terraform CLI found${NC}"
fi

if ! command_exists az; then
    echo -e "${RED}❌ Azure CLI not found. Please install Azure CLI${NC}"
    prereqs_ok=false
else
    echo -e "${GREEN}✅ Azure CLI found${NC}"
fi

if ! command_exists git; then
    echo -e "${RED}❌ Git not found. Please install Git${NC}"
    prereqs_ok=false
else
    echo -e "${GREEN}✅ Git found${NC}"
fi

if ! command_exists python3; then
    echo -e "${RED}❌ Python3 not found. Please install Python3${NC}"
    prereqs_ok=false
else
    echo -e "${GREEN}✅ Python3 found${NC}"
fi

if [ "$prereqs_ok" = false ]; then
    echo -e "${RED}❌ Prerequisites not met. Please install missing tools.${NC}"
    exit 1
fi

# Check Azure login
echo -e "${BLUE}🔐 Checking Azure Authentication...${NC}"
if account=$(az account show --query "name" -o tsv 2>/dev/null); then
    echo -e "${GREEN}✅ Logged into Azure as: $account${NC}"
else
    echo -e "${YELLOW}❌ Not logged into Azure. Running 'az login'...${NC}"
    az login
fi

if [ "$VALIDATE_ONLY" = true ]; then
    echo -e "${BLUE}🔍 Running validation only...${NC}"
    python3 validate_deployment.py
    exit $?
fi

# Step 1: Deploy Terraform Infrastructure
if [ "$SKIP_TERRAFORM" = false ]; then
    echo -e "${BLUE}🏗️  Step 1: Deploying Terraform Infrastructure${NC}"
    echo -e "${BLUE}=============================================${NC}"
    
    cd automation
    
    run_command "terraform init" "Terraform initialization" || exit 1
    run_command "terraform plan -out=tfplan" "Terraform planning" || exit 1
    
    echo -e "${YELLOW}📋 Terraform plan created. Review the changes above.${NC}"
    read -p "Do you want to apply these changes? (y/N): " confirm
    
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        run_command "terraform apply tfplan" "Terraform apply" || exit 1
        echo -e "${GREEN}✅ Terraform infrastructure deployed successfully!${NC}"
    else
        echo -e "${YELLOW}⏸️  Terraform deployment skipped by user${NC}"
    fi
    
    cd ..
else
    echo -e "${YELLOW}⏭️  Skipping Terraform deployment${NC}"
fi

# Step 2: GitHub Actions Deployment
if [ "$SKIP_GITHUB" = false ]; then
    echo -e "${BLUE}🐙 Step 2: GitHub Actions Deployment${NC}"
    echo -e "${BLUE}====================================${NC}"
    
    echo -e "${YELLOW}📝 Committing and pushing changes...${NC}"
    git add .
    git commit -m "Fix: Resolve Azure Web App deployment issues

- Fix GitHub Actions workflow dependency installation
- Add Azure Voice Live API configuration
- Update application startup configuration  
- Implement security hardening
- Add deployment validation tools" || echo "No changes to commit"
    
    git push origin main
    
    echo -e "${GREEN}✅ Changes pushed to GitHub${NC}"
    echo -e "${CYAN}🔄 GitHub Actions workflow will start automatically${NC}"
    echo -e "${CYAN}📊 Monitor progress at: https://github.com/abs0914/acs-azopenai-voice-integration/actions${NC}"
    
    echo -e "${YELLOW}⏳ Waiting 30 seconds for workflow to start...${NC}"
    sleep 30
else
    echo -e "${YELLOW}⏭️  Skipping GitHub Actions deployment${NC}"
fi

# Step 3: Validation
echo -e "${BLUE}🔍 Step 3: Deployment Validation${NC}"
echo -e "${BLUE}================================${NC}"

echo -e "${YELLOW}⏳ Waiting for application to be ready...${NC}"
sleep 60

echo -e "${YELLOW}🧪 Running deployment validation...${NC}"
python3 validate_deployment.py

echo ""
echo -e "${GREEN}🎉 Deployment Process Complete!${NC}"
echo -e "${GREEN}===============================${NC}"
echo ""
echo -e "${CYAN}📋 Next Steps:${NC}"
echo -e "${NC}1. Monitor GitHub Actions: https://github.com/abs0914/acs-azopenai-voice-integration/actions${NC}"
echo -e "${NC}2. Check Azure portal logs if needed${NC}"
echo -e "${NC}3. Test voice integration with actual phone calls${NC}"
echo -e "${NC}4. Set up monitoring and alerting${NC}"
echo ""
echo -e "${CYAN}🌐 Application URL: https://tf-ai-aivoice-dev-api-68s3.azurewebsites.net${NC}"
echo -e "${CYAN}🏥 Health Check: https://tf-ai-aivoice-dev-api-68s3.azurewebsites.net/api/health${NC}"
