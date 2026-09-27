# Real-time Audio Streaming and Lip Sync Setup Guide

## Overview
This setup enables real-time audio streaming from your Python AI agent to Unity for live lip sync with your VRM model.

## Components Added

### 1. Enhanced Voice.cs
- Added real-time audio streaming support
- Connects to `/audio_stream` endpoint on your server
- Processes JSON messages with base64-encoded audio chunks
- Provides audio analysis data for lip sync (volume, pitch, spectrum)
- Maintains backward compatibility with WAV file system

### 2. StreamingDownloadHandler (New)
- Custom Unity download handler for processing streaming data
- Handles continuous data reception from the audio stream endpoint

## Setup Instructions

### 1. Unity Setup
1. Attach the enhanced `Voice.cs` script to your audio GameObject
2. Configure uLipSync to use the AudioSource from your Voice.cs script
3. uLipSync will automatically handle the lip sync analysis and VRM blend shape mapping

### 2. uLipSync Integration
Since you're already using uLipSync:
- Make sure uLipSync's audio source is set to the same AudioSource that Voice.cs uses
- uLipSync will automatically detect and analyze the streaming audio
- No additional configuration needed - uLipSync handles VRM blend shapes automatically
- The real-time streaming audio will work seamlessly with uLipSync's analysis

### 3. Server Configuration
Your Python server (app.py) already supports the streaming endpoints:
- `/audio_stream` - WebSocket-like connection for real-time audio
- Audio chunks are sent as JSON with base64-encoded audio data

## How It Works

### Audio Pipeline
1. Python AI generates audio using GPT-SoVITS
2. Audio is chunked and base64-encoded
3. Sent to Unity via `/audio_stream` endpoint as JSON messages
4. Unity receives, decodes, and plays audio in real-time
5. uLipSync automatically analyzes the audio and applies lip sync to your VRM model

### Message Types
- `audio_start`: Signals beginning of new audio stream
- `audio_chunk`: Contains base64-encoded audio data
- `audio_end`: Signals end of audio stream

## Customization

### uLipSync Settings
Adjust uLipSync parameters for better lip sync:
- Microphone sensitivity in uLipSync components
- Blend shape multipliers for more/less pronounced mouth movements
- Smoothing settings for natural transitions

## Troubleshooting

### No Audio Stream
- Check server URL is correctly set in Unity
- Verify app.exe server is running
- Check Unity console for connection errors

### No Lip Sync
- Verify uLipSync is configured to use the correct AudioSource
- Check that uLipSync components are properly set up on your VRM
- Make sure the VRM blend shapes are correctly mapped in uLipSync
- Check uLipSync's microphone sensitivity settings

### Audio Delay/Stuttering
- Reduce audio chunk size in Python if possible
- Adjust Unity's audio buffer settings
- Check network latency between Python and Unity

## Performance Notes
- The streaming system uses Unity's AudioClip.Create with streaming enabled
- Audio chunks are queued and processed in real-time
- uLipSync handles all lip sync analysis automatically
- Real-time streaming works seamlessly with uLipSync's audio analysis

## Integration with uLipSync and VRM
1. Make sure uLipSync is properly set up with your VRM model
2. Configure uLipSync to use the AudioSource from your Voice.cs GameObject
3. The streaming audio will automatically be analyzed by uLipSync
4. uLipSync will handle all VRM blend shape mapping automatically
5. Test the setup with streaming audio - no additional configuration needed!
