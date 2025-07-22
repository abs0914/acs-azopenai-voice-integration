# 🔧 Webhook Setup Guide - Fix "Unable to Complete Call" Error

## 🚨 **Issue Identified**
The error "Sorry we are unable to complete your call at this time" occurs because Azure Communication Services doesn't have a webhook endpoint configured to handle incoming calls.

**Your Voice Live integration is working perfectly** - we just need to set up the webhook for incoming calls.

## 🎯 **Solution: Configure EventGrid Webhook**

### **Step 1: Create Public Endpoint**

Choose one of these options to expose your application:

#### Option A: Dev Tunnels (Recommended for Testing)
```bash
# Open a new PowerShell window as Administrator
devtunnel create --allow-anonymous
devtunnel port create -p 8000
devtunnel host
```

#### Option B: ngrok (Alternative)
```bash
# Download ngrok from https://ngrok.com/download
# Install and run:
ngrok http 8000
```

#### Option C: Manual Port Forwarding
If you have a router, configure port forwarding for port 8000 to your machine's IP.

### **Step 2: Get Your Public URL**

After running one of the above, you'll get a public URL like:
- Dev Tunnels: `https://abc123-8000.devtunnels.ms`
- ngrok: `https://abc123.ngrok.io`

### **Step 3: Configure EventGrid Subscription**

Run this command with your public URL:

```bash
az eventgrid event-subscription create \
  --name "vida-voicebot-incoming-calls" \
  --source-resource-id "/subscriptions/36ff442e-6bb5-4eaf-a58c-f2cde9fee71f/resourceGroups/vida-voice-integration-rg/providers/Microsoft.Communication/communicationServices/vida-voicebot" \
  --endpoint "https://YOUR_PUBLIC_URL/api/incomingCall" \
  --included-event-types "Microsoft.Communication.IncomingCall"
```

**Replace `YOUR_PUBLIC_URL` with your actual public URL from Step 2.**

### **Step 4: Update Environment Configuration**

Update your `.env` file:
```bash
CALLBACK_URI_HOST="https://YOUR_PUBLIC_URL"
```

### **Step 5: Restart Application**

Restart your application to pick up the new configuration:
```bash
python main.py
```

## 🧪 **Testing Steps**

### 1. Verify Webhook Endpoint
Test that your webhook is accessible:
```bash
curl https://YOUR_PUBLIC_URL/api/incomingCall
```

### 2. Test Voice Live Integration
```bash
curl https://YOUR_PUBLIC_URL/api/testVoiceLive
```

### 3. Test Phone Call
Call **+18449197485** - it should now work!

## 🔍 **Troubleshooting**

### Common Issues:

#### 1. "Unable to complete call" persists
- **Check**: EventGrid subscription is created correctly
- **Verify**: Public URL is accessible from internet
- **Confirm**: Webhook endpoint responds to POST requests

#### 2. Application not receiving events
- **Check**: EventGrid subscription endpoint URL is correct
- **Verify**: Application is running and accessible
- **Test**: Manual webhook call works

#### 3. Voice Live not activating
- **Check**: Application logs for Voice Live session creation
- **Verify**: WebSocket connection to Voice Live API
- **Test**: `/api/testVoiceLive` endpoint

## 📋 **Quick Setup Commands**

Here's the complete setup in order:

```bash
# 1. Start your application (if not already running)
cd C:\Users\USER\acs-azopenai-voice-integration\api
python main.py

# 2. In a new terminal, create tunnel
devtunnel create --allow-anonymous
devtunnel port create -p 8000
devtunnel host

# 3. Note the public URL (e.g., https://abc123-8000.devtunnels.ms)

# 4. Create EventGrid subscription (replace URL)
az eventgrid event-subscription create \
  --name "vida-voicebot-incoming-calls" \
  --source-resource-id "/subscriptions/36ff442e-6bb5-4eaf-a58c-f2cde9fee71f/resourceGroups/vida-voice-integration-rg/providers/Microsoft.Communication/communicationServices/vida-voicebot" \
  --endpoint "https://YOUR_PUBLIC_URL/api/incomingCall" \
  --included-event-types "Microsoft.Communication.IncomingCall"

# 5. Test the phone number
# Call +18449197485
```

## ✅ **Expected Result**

After completing these steps:

1. **Call +18449197485**
2. **You should hear**: A greeting from your vida-voice-bot agent
3. **Voice Live Features**: Low-latency, natural conversation with noise suppression
4. **Application Logs**: Should show Voice Live session creation and management

## 🎉 **Success Indicators**

When working correctly, you'll see these logs:
```
Connected to Azure Voice Live API: wss://vida-voice-live.cognitiveservices.azure.com/voice-agent/realtime
Created Voice Live session for call [call-id]
Configured Voice Live session for call [call-id]
Voice Live session updated for call [call-id]
```

## 📞 **Ready to Test!**

Once you complete the webhook setup, your Azure AI Voice Live integration will be fully operational for incoming calls to **+18449197485**!

The Voice Live integration itself is working perfectly - this is just the final step to connect incoming calls to your application.
