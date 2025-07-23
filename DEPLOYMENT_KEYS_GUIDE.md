# 🔑 Azure Web App Deployment Keys Configuration Guide

## Overview
This guide shows you exactly how to add the actual API keys and deploy the Azure Web App "tf-ai-aivoice-dev-api-68s3" with all the fixes implemented.

## 📋 Keys Already Configured

Based on your memory, I've already configured the following keys:

### ✅ Azure Voice Live API Key
**Location**: `automation/terraform.tfvars`
**Status**: ✅ **CONFIGURED**
```
azure_voice_live_api_key = "D0ccvKqf20m8g8wXHnqyF7BFypUJygfQXrjIOm2kMfJASaNvXKu0JQQJ99BGACHYHv6XJ3w3AAAAACOGv7Z2"
```

### ✅ Azure Voice Live Endpoint
**Location**: `automation/app.tf`
**Status**: ✅ **CONFIGURED**
```
AZURE_VOICE_LIVE_ENDPOINT = "https://vida-voice-live.cognitiveservices.azure.com/"
```

### ✅ Voice Bot Assistant ID
**Location**: `automation/app.tf`
**Status**: ✅ **CONFIGURED**
```
VIDA_VOICE_BOT_ASSISTANT_ID = "asst_dEODj1Hu6Z68Ebggl13DAHPv"
```

## 🚀 Deployment Options

You have **3 ways** to deploy:

### Option 1: Automated Deployment (Recommended)

**For Windows (PowerShell):**
```powershell
.\deploy_complete_solution.ps1
```

**For Linux/Mac (Bash):**
```bash
./deploy_complete_solution.sh
```

**What this does:**
- ✅ Checks prerequisites (Terraform, Azure CLI, Git)
- ✅ Verifies Azure authentication
- ✅ Deploys Terraform infrastructure
- ✅ Commits and pushes changes to GitHub
- ✅ Triggers GitHub Actions deployment
- ✅ Validates the deployment

### Option 2: Manual Step-by-Step

#### Step 1: Deploy Terraform Infrastructure
```bash
cd automation
terraform init
terraform plan
terraform apply
cd ..
```

#### Step 2: Commit and Push Changes
```bash
git add .
git commit -m "Fix: Resolve Azure Web App deployment issues"
git push origin main
```

#### Step 3: Monitor GitHub Actions
- Go to: https://github.com/abs0914/acs-azopenai-voice-integration/actions
- Watch the "Build and deploy Python app" workflow

#### Step 4: Validate Deployment
```bash
python validate_deployment.py
```

### Option 3: Validation Only
If you just want to test the current deployment:

**Windows:**
```powershell
.\deploy_complete_solution.ps1 -ValidateOnly
```

**Linux/Mac:**
```bash
./deploy_complete_solution.sh --validate-only
```

## 🔧 Additional Keys You May Need

### GitHub Publish Profile Secret
**Status**: ⚠️ **NEEDS VERIFICATION**

1. Go to Azure Portal → App Services → tf-ai-aivoice-dev-api-68s3
2. Click "Get publish profile" and download the file
3. Go to GitHub → Settings → Secrets and variables → Actions
4. Add/update secret: `AZUREAPPSERVICE_PUBLISHPROFILE_AAE6AA404B8142678BCB0554013EC3B9`
5. Paste the entire contents of the publish profile file

### Optional: Azure OpenAI Keys (Fallback)
**Status**: ✅ **CONFIGURED VIA TERRAFORM**

These are automatically configured through Terraform:
- `AZURE_OPENAI_SERVICE_KEY` - From Terraform cognitive account
- `AZURE_OPENAI_SERVICE_ENDPOINT` - From Terraform cognitive account
- `OPENAI_ASSISTANT_ID` - Set to "asst_dEODj1Hu6Z68Ebggl13DAHPv"

## 🔍 Verification Steps

After deployment, verify these endpoints:

### 1. Basic Health Check
```
GET https://tf-ai-aivoice-dev-api-68s3.azurewebsites.net/api/health
Expected: 200 OK
```

### 2. Voice Live Integration Test
```
GET https://tf-ai-aivoice-dev-api-68s3.azurewebsites.net/api/testVoiceLive
Expected: 200 OK with Voice Live connection status
```

### 3. Root Endpoint
```
GET https://tf-ai-aivoice-dev-api-68s3.azurewebsites.net/
Expected: 200 OK
```

## 🚨 Troubleshooting

### If Terraform Fails
```bash
# Check Azure login
az account show

# Re-initialize if needed
cd automation
terraform init -upgrade
terraform plan
```

### If GitHub Actions Fails
1. Check the publish profile secret is configured
2. Verify Azure credentials in GitHub
3. Check build logs for specific errors

### If Application Won't Start
1. Check Azure Portal → App Services → tf-ai-aivoice-dev-api-68s3 → Log stream
2. Verify environment variables in Configuration → Application settings
3. Check startup command in Configuration → General settings

### If Voice Live Integration Fails
1. Verify API key is correct in Azure Portal
2. Test endpoint connectivity: `curl https://vida-voice-live.cognitiveservices.azure.com/`
3. Check application logs for WebSocket errors

## 📊 Expected Timeline

- **Terraform deployment**: 5-10 minutes
- **GitHub Actions build**: 2-3 minutes
- **Application startup**: 1-2 minutes
- **Total time**: ~15 minutes

## 🎯 Success Indicators

You'll know it's working when:
- ✅ Terraform apply completes without errors
- ✅ GitHub Actions workflow shows green checkmark
- ✅ Health endpoint returns 200 OK
- ✅ Voice Live test endpoint responds successfully
- ✅ Azure portal shows app as "Running"

## 📞 Ready to Deploy?

**Your keys are already configured!** You can proceed with deployment using any of the options above.

**Recommended next step:**
```powershell
# Windows
.\deploy_complete_solution.ps1

# Or Linux/Mac
./deploy_complete_solution.sh
```

This will handle everything automatically and validate the deployment for you.
