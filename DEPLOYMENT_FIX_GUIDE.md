# Azure Web App Deployment Fix Guide

## 🚨 Critical Issues Resolved

This guide documents the fixes implemented to resolve the deployment failures for Azure Web App "tf-ai-aivoice-dev-api-68s3".

## ✅ Changes Made

### 1. GitHub Actions Workflow Fix
**File**: `.github/workflows/main_tf-ai-aivoice-dev-api-68s3.yml`

**Problem**: Build failed because workflow tried to install dependencies from root `requirements.txt` but the actual file is in `api/requirements.txt`.

**Fix Applied**:
```yaml
- name: Install dependencies
  run: |
    cd api
    pip install -r requirements.txt
```

**Impact**: Resolves build failures that prevented all deployments.

### 2. Azure Voice Live API Configuration
**Files**: `automation/app.tf`, `automation/variables.tf`, `automation/terraform.tfvars`

**Problem**: Missing critical environment variables for Azure Voice Live API integration.

**Fix Applied**:
```terraform
# In app.tf - Added to app_settings
AZURE_VOICE_LIVE_ENDPOINT          = "https://vida-voice-live.cognitiveservices.azure.com/"
AZURE_VOICE_LIVE_API_KEY           = var.azure_voice_live_api_key
AZURE_VOICE_LIVE_DEPLOYMENT        = "gpt-4o-realtime-preview"
AZURE_VOICE_LIVE_REGION            = "eastus2"
VIDA_VOICE_BOT_ASSISTANT_ID        = "asst_dEODj1Hu6Z68Ebggl13DAHPv"
```

**Impact**: Enables the core voice integration functionality.

### 3. Application Startup Configuration
**Files**: `automation/locals.tf`, `startup.sh`

**Problem**: Incorrect startup command that didn't account for application structure.

**Fix Applied**:
```terraform
# In locals.tf
api_command_line = "bash startup.sh"
```

```bash
# In startup.sh
#!/bin/bash
cd /home/site/wwwroot
export PYTHONPATH=/home/site/wwwroot:$PYTHONPATH
cd api
gunicorn --bind 0.0.0.0:8000 --workers 1 --timeout 600 main:app
```

**Impact**: Ensures application starts correctly with proper working directory.

### 4. Security Hardening
**File**: `automation/app.tf`

**Problem**: CORS configured with wildcard (*) - security risk.

**Fix Applied**:
```terraform
# Replace wildcard CORS with specific allowed origins
API_ALLOW_ORIGINS='https://*.azurewebsites.net,https://*.azure.com,https://localhost:*'
```

**Impact**: Improves security while maintaining functionality.

## 🚀 Deployment Instructions

### Step 1: Update Terraform Configuration
1. Navigate to the `automation/` directory
2. Update `terraform.tfvars` with your actual Azure Voice Live API key:
   ```
   azure_voice_live_api_key = "YOUR_ACTUAL_API_KEY_HERE"
   ```

### Step 2: Deploy Infrastructure
```bash
cd automation
terraform init
terraform plan
terraform apply
```

### Step 3: Trigger GitHub Actions Deployment
1. Go to GitHub repository
2. Navigate to Actions tab
3. Select "Build and deploy Python app to Azure Web App"
4. Click "Run workflow" to trigger manual deployment

### Step 4: Verify Deployment
1. Check GitHub Actions logs for successful completion
2. Visit the Azure Web App URL
3. Test health endpoint: `https://tf-ai-aivoice-dev-api-68s3.azurewebsites.net/api/health`
4. Test Voice Live integration: `https://tf-ai-aivoice-dev-api-68s3.azurewebsites.net/api/testVoiceLive`

## 🔍 Verification Checklist

- [ ] GitHub Actions workflow completes successfully
- [ ] Application starts without errors in Azure portal logs
- [ ] Health check endpoint returns 200 OK
- [ ] Environment variables are properly set in Azure portal
- [ ] Voice Live API integration is functional
- [ ] ACS phone number configuration is correct

## 🐛 Troubleshooting

### If GitHub Actions Still Fails
1. Check that the publish profile secret is configured in GitHub
2. Verify Azure credentials have proper permissions
3. Check build logs for specific error messages

### If Application Won't Start
1. Check Azure portal logs under "Log stream"
2. Verify all environment variables are set
3. Ensure startup.sh has execute permissions

### If Voice Live Integration Fails
1. Verify Azure Voice Live API key is correct
2. Check network connectivity to Voice Live endpoint
3. Review application logs for WebSocket connection errors

## 📊 Expected Results

After implementing these fixes:
- ✅ GitHub Actions builds complete successfully
- ✅ Application deploys and starts correctly
- ✅ All environment variables are configured
- ✅ Voice Live API integration is functional
- ✅ Security configurations are hardened
- ✅ Health checks pass

## 🔄 Next Steps

1. **Monitor**: Set up Application Insights alerts
2. **Test**: Perform end-to-end voice integration testing
3. **Optimize**: Implement performance monitoring
4. **Scale**: Configure auto-scaling if needed

## 📞 Support

If issues persist after implementing these fixes:
1. Check Azure portal logs for detailed error messages
2. Review GitHub Actions logs for build failures
3. Verify all configuration values are correct
4. Test individual components (ACS, OpenAI, Voice Live) separately
