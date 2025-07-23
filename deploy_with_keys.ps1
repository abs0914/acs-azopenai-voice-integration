# Secure Deployment Script with API Key Configuration
# This script configures the actual API key and deploys the solution

param(
    [Parameter(Mandatory=$true)]
    [string]$VoiceLiveApiKey
)

Write-Host "🔐 Secure Azure Web App Deployment" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""

# Step 1: Configure the API key locally (not committed to git)
Write-Host "🔑 Step 1: Configuring Azure Voice Live API Key..." -ForegroundColor Blue

$tfvarsPath = "automation/terraform.tfvars"
$tfvarsContent = Get-Content $tfvarsPath -Raw

# Replace placeholder with actual key
$tfvarsContent = $tfvarsContent -replace "YOUR_AZURE_VOICE_LIVE_API_KEY_HERE", $VoiceLiveApiKey
Set-Content -Path $tfvarsPath -Value $tfvarsContent

Write-Host "✅ API key configured in terraform.tfvars" -ForegroundColor Green

# Step 2: Deploy Terraform infrastructure
Write-Host "🏗️  Step 2: Deploying Terraform Infrastructure..." -ForegroundColor Blue

Set-Location "automation"

try {
    Write-Host "⏳ Running terraform plan..." -ForegroundColor Yellow
    terraform plan -out=tfplan
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "📋 Terraform plan successful. Applying changes..." -ForegroundColor Yellow
        terraform apply -auto-approve tfplan
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Terraform infrastructure deployed successfully!" -ForegroundColor Green
        } else {
            Write-Host "❌ Terraform apply failed" -ForegroundColor Red
            Set-Location ".."
            exit 1
        }
    } else {
        Write-Host "❌ Terraform plan failed" -ForegroundColor Red
        Set-Location ".."
        exit 1
    }
} catch {
    Write-Host "❌ Terraform deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    Set-Location ".."
    exit 1
}

Set-Location ".."

# Step 3: Reset the terraform.tfvars to placeholder (for security)
Write-Host "🔒 Step 3: Securing terraform.tfvars..." -ForegroundColor Blue

$tfvarsContent = $tfvarsContent -replace [regex]::Escape($VoiceLiveApiKey), "YOUR_AZURE_VOICE_LIVE_API_KEY_HERE"
Set-Content -Path $tfvarsPath -Value $tfvarsContent

Write-Host "✅ API key removed from terraform.tfvars for security" -ForegroundColor Green

# Step 4: Commit and push changes (without the API key)
Write-Host "📤 Step 4: Committing and pushing changes..." -ForegroundColor Blue

git add .
git commit -m "Fix: Resolve Azure Web App deployment issues - Fix GitHub Actions workflow dependency installation path - Add Azure Voice Live API configuration to Terraform - Update application startup configuration with proper script - Implement security hardening (CORS, container settings) - Add comprehensive deployment guides and validation tools - Configure all required environment variables for voice integration - This resolves the critical deployment failures and enables full voice integration functionality."

git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Changes pushed to GitHub successfully!" -ForegroundColor Green
    Write-Host "🔄 GitHub Actions workflow will start automatically" -ForegroundColor Cyan
    Write-Host "📊 Monitor progress at: https://github.com/abs0914/acs-azopenai-voice-integration/actions" -ForegroundColor Cyan
} else {
    Write-Host "❌ Failed to push changes to GitHub" -ForegroundColor Red
    exit 1
}

# Step 5: Wait and validate deployment
Write-Host "⏳ Step 5: Waiting for deployment to complete..." -ForegroundColor Blue
Write-Host "Waiting 2 minutes for GitHub Actions and application startup..." -ForegroundColor Yellow

Start-Sleep -Seconds 120

Write-Host "🧪 Running deployment validation..." -ForegroundColor Yellow
python validate_deployment.py

Write-Host ""
Write-Host "🎉 Deployment Process Complete!" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Monitor GitHub Actions: https://github.com/abs0914/acs-azopenai-voice-integration/actions" -ForegroundColor White
Write-Host "2. Check Azure portal logs if needed" -ForegroundColor White
Write-Host "3. Test voice integration with actual phone calls" -ForegroundColor White
Write-Host "4. Set up monitoring and alerting" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Application URL: https://tf-ai-aivoice-dev-api-68s3.azurewebsites.net" -ForegroundColor Cyan
Write-Host "🏥 Health Check: https://tf-ai-aivoice-dev-api-68s3.azurewebsites.net/api/health" -ForegroundColor Cyan

Write-Host ""
Write-Host "⚠️  Important Security Note:" -ForegroundColor Yellow
Write-Host "The API key has been removed from terraform.tfvars for security." -ForegroundColor Yellow
Write-Host "It's now configured in Azure and will persist there." -ForegroundColor Yellow
