# Complete Deployment Script for Azure Web App tf-ai-aivoice-dev-api-68s3
# This script handles the complete deployment process

param(
    [switch]$SkipTerraform,
    [switch]$SkipGitHub,
    [switch]$ValidateOnly
)

Write-Host "🚀 Azure Web App Deployment Script" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "Web App: tf-ai-aivoice-dev-api-68s3" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Function to run command with error handling
function Invoke-SafeCommand($command, $description) {
    Write-Host "⏳ $description..." -ForegroundColor Yellow
    try {
        Invoke-Expression $command
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $description completed successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ $description failed with exit code $LASTEXITCODE" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ $description failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Check prerequisites
Write-Host "🔍 Checking Prerequisites..." -ForegroundColor Blue
$prereqsOk = $true

if (-not (Test-Command "terraform")) {
    Write-Host "❌ Terraform not found. Please install Terraform CLI" -ForegroundColor Red
    $prereqsOk = $false
} else {
    Write-Host "✅ Terraform CLI found" -ForegroundColor Green
}

if (-not (Test-Command "az")) {
    Write-Host "❌ Azure CLI not found. Please install Azure CLI" -ForegroundColor Red
    $prereqsOk = $false
} else {
    Write-Host "✅ Azure CLI found" -ForegroundColor Green
}

if (-not (Test-Command "git")) {
    Write-Host "❌ Git not found. Please install Git" -ForegroundColor Red
    $prereqsOk = $false
} else {
    Write-Host "✅ Git found" -ForegroundColor Green
}

if (-not $prereqsOk) {
    Write-Host "❌ Prerequisites not met. Please install missing tools." -ForegroundColor Red
    exit 1
}

# Check Azure login
Write-Host "🔐 Checking Azure Authentication..." -ForegroundColor Blue
try {
    $account = az account show --query "name" -o tsv 2>$null
    if ($account) {
        Write-Host "✅ Logged into Azure as: $account" -ForegroundColor Green
    } else {
        Write-Host "❌ Not logged into Azure. Running 'az login'..." -ForegroundColor Yellow
        az login
    }
} catch {
    Write-Host "❌ Azure authentication failed" -ForegroundColor Red
    exit 1
}

if ($ValidateOnly) {
    Write-Host "🔍 Running validation only..." -ForegroundColor Blue
    python validate_deployment.py
    exit $LASTEXITCODE
}

# Step 1: Deploy Terraform Infrastructure
if (-not $SkipTerraform) {
    Write-Host "🏗️  Step 1: Deploying Terraform Infrastructure" -ForegroundColor Blue
    Write-Host "=============================================" -ForegroundColor Blue
    
    Set-Location "automation"
    
    if (-not (Invoke-SafeCommand "terraform init" "Terraform initialization")) {
        exit 1
    }
    
    if (-not (Invoke-SafeCommand "terraform plan -out=tfplan" "Terraform planning")) {
        exit 1
    }
    
    Write-Host "📋 Terraform plan created. Review the changes above." -ForegroundColor Yellow
    $confirm = Read-Host "Do you want to apply these changes? (y/N)"
    
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        if (-not (Invoke-SafeCommand "terraform apply tfplan" "Terraform apply")) {
            exit 1
        }
        Write-Host "✅ Terraform infrastructure deployed successfully!" -ForegroundColor Green
    } else {
        Write-Host "⏸️  Terraform deployment skipped by user" -ForegroundColor Yellow
    }
    
    Set-Location ".."
} else {
    Write-Host "⏭️  Skipping Terraform deployment" -ForegroundColor Yellow
}

# Step 2: GitHub Actions Deployment
if (-not $SkipGitHub) {
    Write-Host "🐙 Step 2: GitHub Actions Deployment" -ForegroundColor Blue
    Write-Host "====================================" -ForegroundColor Blue
    
    Write-Host "📝 Committing and pushing changes..." -ForegroundColor Yellow
    git add .
    git commit -m "Fix: Resolve Azure Web App deployment issues

- Fix GitHub Actions workflow dependency installation
- Add Azure Voice Live API configuration
- Update application startup configuration  
- Implement security hardening
- Add deployment validation tools"
    
    git push origin main
    
    Write-Host "✅ Changes pushed to GitHub" -ForegroundColor Green
    Write-Host "🔄 GitHub Actions workflow will start automatically" -ForegroundColor Cyan
    Write-Host "📊 Monitor progress at: https://github.com/abs0914/acs-azopenai-voice-integration/actions" -ForegroundColor Cyan
    
    Write-Host "⏳ Waiting 30 seconds for workflow to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
} else {
    Write-Host "⏭️  Skipping GitHub Actions deployment" -ForegroundColor Yellow
}

# Step 3: Validation
Write-Host "🔍 Step 3: Deployment Validation" -ForegroundColor Blue
Write-Host "================================" -ForegroundColor Blue

Write-Host "⏳ Waiting for application to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

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
