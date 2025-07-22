# Azure AI Voice Live Integration Guide

## Overview

This document describes the implementation of Azure AI Voice Live API integration with Azure Communication Services for real-time voice agent interactions. The integration replaces the traditional STT/TTS approach with a direct audio-to-audio streaming solution for lower latency and enhanced voice capabilities.

## Architecture Changes

### Before (Traditional Approach)
- **Audio Input**: ACS Call → Speech Recognition → Text
- **Processing**: Text → OpenAI Assistant API → Text Response  
- **Audio Output**: Text → Text-to-Speech → ACS Call
- **Latency**: Higher due to multiple conversion steps
- **Features**: Basic speech recognition and synthesis

### After (Voice Live Integration)
- **Audio Input**: ACS Call → Bidirectional Audio Stream → Voice Live API
- **Processing**: Direct audio processing with integrated AI models
- **Audio Output**: Voice Live API → Bidirectional Audio Stream → ACS Call
- **Latency**: Significantly reduced with direct audio-to-audio processing
- **Features**: Advanced noise suppression, echo cancellation, interruption detection

## Key Components

### 1. VoiceLiveService (`api/src/services/voice_live_service.py`)
- Manages WebSocket connections to Azure AI Voice Live API
- Handles session configuration and management
- Integrates with vida-voice-bot agent (ID: asst_dEODj1Hu6Z68Ebggl13DAHPv)

### 2. AudioStreamingService (`api/src/services/audio_streaming_service.py`)
- Manages bidirectional audio streaming between ACS and Voice Live API
- Handles media streaming events and audio data forwarding
- Provides fallback to traditional approach if Voice Live fails

### 3. Updated EventHandlers (`api/src/core/event_handlers.py`)
- Modified to use Voice Live integration for call handling
- Maintains backward compatibility with traditional approach
- Handles media streaming events and call lifecycle management

## Configuration

### Environment Variables
```bash
# Azure AI Voice Live API
AZURE_VOICE_LIVE_ENDPOINT="https://vida-voice-live.cognitiveservices.azure.com/"
AZURE_VOICE_LIVE_API_KEY="D0ccvKqf20m8g8wXHnqyF7BFypUJygfQXrjIOm2kMfJASaNvXKu0JQQJ99BGACHYHv6XJ3w3AAAAACOGv7Z2"
AZURE_VOICE_LIVE_DEPLOYMENT="gpt-4o-realtime-preview"
AZURE_VOICE_LIVE_REGION="eastus2"
VIDA_VOICE_BOT_ASSISTANT_ID="asst_dEODj1Hu6Z68Ebggl13DAHPv"
```

### Voice Live Session Configuration
```python
session_config = {
    "turn_detection": {
        "type": "azure_semantic_vad",
        "threshold": 0.3,
        "prefix_padding_ms": 200,
        "silence_duration_ms": 200,
        "remove_filler_words": False,
        "end_of_utterance_detection": {
            "model": "semantic_detection_v1",
            "threshold": 0.1,
            "timeout": 4,
        },
    },
    "input_audio_noise_reduction": {"type": "azure_deep_noise_suppression"},
    "input_audio_echo_cancellation": {"type": "server_echo_cancellation"},
    "voice": {
        "name": "en-US-Aria:DragonHDLatestNeural",
        "type": "azure-standard",
        "temperature": 0.8,
    },
}
```

## Implementation Flow

### 1. Call Connected Event
1. Initialize conversation state in cache
2. Start bidirectional audio streaming with ACS
3. Create Voice Live session with WebSocket connection
4. Configure session with vida-voice-bot agent
5. Begin real-time audio processing

### 2. Audio Processing
1. **Incoming Audio**: ACS → Audio Streaming Service → Voice Live API
2. **AI Processing**: Voice Live API processes audio with integrated models
3. **Outgoing Audio**: Voice Live API → Audio Streaming Service → ACS

### 3. Call Disconnected Event
1. Stop bidirectional audio streaming
2. Close Voice Live WebSocket connection
3. Clean up cache and resources

## Benefits

### Performance Improvements
- **Reduced Latency**: Direct audio-to-audio processing eliminates conversion steps
- **Better Audio Quality**: Built-in noise suppression and echo cancellation
- **Natural Interruptions**: Advanced interruption detection and handling

### Enhanced Features
- **Semantic Voice Activity Detection**: More accurate turn detection
- **Deep Noise Suppression**: Improved audio clarity in noisy environments
- **Server Echo Cancellation**: Prevents feedback loops
- **Advanced End-of-Turn Detection**: Natural conversation flow

### Scalability
- **Managed Infrastructure**: No need to deploy or manage AI models
- **Multiple Model Support**: GPT-4o, GPT-4o-mini, and Phi models available
- **Global Availability**: Supports 15+ locales and 600+ voices

## Fallback Strategy

The implementation includes a fallback mechanism to the traditional STT/TTS approach if Voice Live integration fails:

```python
async def _fallback_to_traditional_approach(self, call_connection_id: str, participant_id: str, payload_dict: dict):
    """Fallback to traditional STT/TTS approach if Voice Live fails"""
    # Uses existing call_handler.handle_recognize() method
    # Maintains conversation continuity
```

## Testing and Validation

### Prerequisites
1. Azure Communication Services resource with phone number
2. Azure AI Voice Live API access and credentials
3. vida-voice-bot assistant configured
4. Dev tunnel or public endpoint for webhooks

### Test Scenarios
1. **Basic Voice Interaction**: Call the ACS phone number and verify Voice Live response
2. **Noise Suppression**: Test in noisy environment to verify audio enhancement
3. **Interruption Handling**: Test natural conversation interruptions
4. **Fallback Testing**: Simulate Voice Live failure to test traditional approach

## Monitoring and Logging

The implementation includes comprehensive logging for:
- Voice Live session creation and management
- Audio streaming events and data flow
- Error handling and fallback scenarios
- Performance metrics and latency tracking

## Next Steps

1. **Performance Optimization**: Fine-tune Voice Live session parameters
2. **Custom Voice Integration**: Implement branded voice models
3. **Avatar Support**: Add visual avatar integration
4. **Analytics**: Implement conversation analytics and insights
5. **Multi-language Support**: Expand to additional locales and languages

## Troubleshooting

### Common Issues
1. **WebSocket Connection Failures**: Check endpoint URL and API key
2. **Audio Quality Issues**: Verify noise suppression and echo cancellation settings
3. **High Latency**: Review network connectivity and session configuration
4. **Fallback Activation**: Check Voice Live API availability and credentials

### Debug Logging
Enable debug logging to troubleshoot issues:
```python
import logging
logging.getLogger('voice_live_service').setLevel(logging.DEBUG)
logging.getLogger('audio_streaming_service').setLevel(logging.DEBUG)
```

## References

- [Azure AI Voice Live API Documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live)
- [Azure Communication Services Call Automation](https://learn.microsoft.com/en-us/azure/communication-services/concepts/call-automation/)
- [Microsoft Sample Implementation](https://github.com/Azure-Samples/communication-services-dotnet-quickstarts/tree/main/CallAutomation_AzureAI_VoiceLive)
