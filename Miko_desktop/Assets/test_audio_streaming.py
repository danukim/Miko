"""
Test script for audio streaming to Unity server
Tests the audio streaming functionality with a simple "Hello how are you!" message
"""

import os
import sys
import time
import numpy as np
import warnings

# Add the path where your main scripts are located
sys.path.append(r"c:\Users\danu0\Downloads\OneReality")

# Import the audio streaming module
try:
    from audio_streamer import create_mitsuha_audio_handler
except ImportError:
    print("❌ Could not import audio_streamer. Make sure the file is in the correct path.")
    sys.exit(1)

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

def test_audio_streaming():
    """Test audio streaming with GPT-SoVITS TTS"""
    
    print("🎵 Testing Audio Streaming to Unity Server...")
    print("=" * 50)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv(r"c:\Users\danu0\Downloads\OneReality\.env")
    except ImportError:
        print("❌ python-dotenv not found. Please install it: pip install python-dotenv")
        return False
    
    # Get server IP from environment
    server_ip = os.getenv("IP_ADDRESS", "localhost")
    server_url = f"http://{server_ip}:8000"
    
    print(f"🌐 Server URL: {server_url}")
    
    # Test message
    test_message = "Hello how are you!"
    print(f"💬 Test message: '{test_message}'")
    
    try:
        # Initialize GPT-SoVITS
        print("🎤 Initializing GPT-SoVITS...")
        
        # Import GPT-SoVITS modules
        sys.path.append(r"c:\Users\danu0\Downloads\OneReality\GPT-SoVITS")
        from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
        
        # GPT-SoVITS configuration paths from environment
        config_path = os.getenv("GPT_SOVITS_CONFIG_PATH")
        t2s_ckpt = os.getenv("GPT_SOVITS_T2S_CKPT")
        vits_ckpt = os.getenv("GPT_SOVITS_VITS_CKPT")
        ref_audio = os.getenv("GPT_SOVITS_REF_AUDIO")
        prompt_text = os.getenv("GPT_SOVITS_PROMPT_TEXT")
        
        # Validate configuration
        if not all([config_path, t2s_ckpt, vits_ckpt, ref_audio, prompt_text]):
            print("❌ Missing GPT-SoVITS configuration in .env file!")
            print("Required variables: GPT_SOVITS_CONFIG_PATH, GPT_SOVITS_T2S_CKPT, GPT_SOVITS_VITS_CKPT, GPT_SOVITS_REF_AUDIO, GPT_SOVITS_PROMPT_TEXT")
            return False
        
        # Initialize TTS
        print("🔧 Loading TTS models...")
        cfg = TTS_Config(config_path)
        tts = TTS(cfg)
        tts.init_t2s_weights(t2s_ckpt)
        tts.init_vits_weights(vits_ckpt)
        print("✅ TTS models loaded successfully!")
        
        # Create audio handler for streaming
        print("🎵 Creating audio handler...")
        audio_handler = create_mitsuha_audio_handler(
            server_url=server_url,
            local_volume=0.0  # Muted for testing - Unity handles playback
        )
        
        # Start audio stream
        sample_rate = 22050
        print(f"🚀 Starting audio stream (Sample rate: {sample_rate}Hz)...")
        audio_handler.start_playback(sample_rate)
        
        # Generate and stream TTS audio
        print("🎤 Generating TTS audio...")
        
        # Generate audio with GPT-SoVITS
        audio_generator = tts.run(
            text=test_message,
            text_lang="en",
            ref_audio_path=ref_audio,
            prompt_text=prompt_text,
            prompt_lang="en",
            top_k=5,
            top_p=1,
            temperature=1,
            text_split_method="cut5",
            batch_size=1,
            media_type="wav",
            speed_factor=1.0,
            ref_text_free=False,
            split_bucket=True,
            fragment_interval=0.3,
            seed=-1,
            keep_random=True,
            parallel_infer=True,
            repetition_penalty=1.35
        )
        
        print("🎵 Streaming audio fragments...")
        fragment_count = 0
        
        for audio_fragment in audio_generator:
            if audio_fragment is not None:
                fragment_count += 1
                print(f"📡 Streaming fragment {fragment_count} (shape: {audio_fragment.shape})")
                
                # Stream to Unity
                audio_handler.add_audio_chunk(audio_fragment)
                
                # Small delay to simulate real-time streaming
                time.sleep(0.1)
        
        print(f"✅ Successfully streamed {fragment_count} audio fragments!")
        
        # Wait a bit for audio to finish playing
        print("⏳ Waiting for audio to finish...")
        time.sleep(2)
        
        # Stop streaming
        print("🛑 Stopping audio stream...")
        audio_handler.stop_playback()
        
        print("🎉 Audio streaming test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure GPT-SoVITS is properly installed and configured.")
        return False
        
    except Exception as e:
        print(f"❌ Error during audio streaming test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_sine_wave():
    """Test streaming with a simple sine wave if TTS fails"""
    
    print("\n🎵 Testing with simple sine wave...")
    print("=" * 50)
    
    try:
        from dotenv import load_dotenv
        load_dotenv(r"c:\Users\danu0\Downloads\OneReality\.env")
    except ImportError:
        print("⚠️ python-dotenv not found, using localhost")
    
    server_ip = os.getenv("IP_ADDRESS", "localhost")
    server_url = f"http://{server_ip}:8000"
    
    try:
        # Create audio handler
        audio_handler = create_mitsuha_audio_handler(
            server_url=server_url,
            local_volume=0.0
        )
        
        # Generate test sine wave
        sample_rate = 22050
        duration = 2.0  # 2 seconds
        frequency = 440  # A4 note
        
        print(f"🎵 Generating {duration}s sine wave at {frequency}Hz...")
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        sine_wave = (np.sin(2 * np.pi * frequency * t) * 0.5).astype(np.float32)
        
        # Start streaming
        audio_handler.start_playback(sample_rate)
        
        # Stream in chunks
        chunk_size = 1024
        chunk_count = 0
        
        print("📡 Streaming sine wave chunks...")
        for i in range(0, len(sine_wave), chunk_size):
            chunk = sine_wave[i:i+chunk_size]
            chunk_count += 1
            
            print(f"📡 Streaming chunk {chunk_count} (size: {len(chunk)})")
            audio_handler.add_audio_chunk(chunk)
            
            # Real-time delay
            time.sleep(chunk_size / sample_rate)
        
        print(f"✅ Streamed {chunk_count} sine wave chunks!")
        
        # Stop streaming
        time.sleep(0.5)
        audio_handler.stop_playback()
        
        print("🎉 Sine wave streaming test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Sine wave test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_animation_commands():
    """Test sending animation commands to Unity"""
    
    print("\n🎭 Testing animation commands...")
    print("=" * 50)
    
    try:
        from dotenv import load_dotenv
        load_dotenv(r"c:\Users\danu0\Downloads\OneReality\.env")
    except ImportError:
        print("⚠️ python-dotenv not found, using localhost")
    
    server_ip = os.getenv("IP_ADDRESS", "localhost")
    server_url = f"http://{server_ip}:8000"
    
    try:
        # Create audio handler
        audio_handler = create_mitsuha_audio_handler(server_url=server_url)
        
        # Test animations
        animations = ["Wave", "Thumbs-up", "Nodding", "Clap"]
        
        for animation in animations:
            print(f"🎭 Sending animation: {animation}")
            audio_handler.send_animation(animation)
            time.sleep(1)  # Wait between animations
        
        print("🎉 Animation commands test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Animation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_connection():
    """Test basic connection to the server"""
    
    print("\n🔌 Testing basic server connection...")
    print("=" * 50)
    
    try:
        import requests
        from dotenv import load_dotenv
        load_dotenv(r"c:\Users\danu0\Downloads\OneReality\.env")
    except ImportError as e:
        print(f"❌ Missing required modules: {e}")
        return False
    
    server_ip = os.getenv("IP_ADDRESS", "localhost")
    server_url = f"http://{server_ip}:8000"
    
    try:
        # Test basic connection
        print(f"🌐 Testing connection to: {server_url}")
        
        test_payload = {
            'type': 'test_connection',
            'message': 'Hello from test script!'
        }
        
        response = requests.post(
            server_url,
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        print(f"📡 Response code: {response.status_code}")
        print(f"📡 Response text: {response.text}")
        
        if response.status_code == 200:
            print("✅ Server connection successful!")
            return True
        else:
            print("⚠️ Server responded but with non-200 status")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Make sure your server is running!")
        print(f"   Expected server at: {server_url}")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MITSUHA Audio Streaming Test Suite")
    print("=" * 60)
    
    # Test 0: Basic connection
    print("\n📋 Test 0: Basic Server Connection")
    connection_success = test_basic_connection()
    
    if not connection_success:
        print("\n❌ Server connection failed. Please:")
        print("   1. Make sure your app.py server is running")
        print("   2. Check the IP_ADDRESS in your .env file")
        print("   3. Verify the server is accessible")
        sys.exit(1)
    
    # Test 1: Full TTS streaming
    print("\n📋 Test 1: TTS Audio Streaming")
    tts_success = test_audio_streaming()
    
    # Test 2: Simple sine wave (fallback or if TTS fails)
    print("\n📋 Test 2: Sine Wave Streaming")
    sine_success = test_simple_sine_wave()
    
    # Test 3: Animation commands
    print("\n📋 Test 3: Animation Commands")
    animation_success = test_animation_commands()
    
    print("\n🏁 Test Summary:")
    print(f"   Connection: {'✅ PASS' if connection_success else '❌ FAIL'}")
    print(f"   TTS Audio:  {'✅ PASS' if tts_success else '❌ FAIL'}")
    print(f"   Sine Wave:  {'✅ PASS' if sine_success else '❌ FAIL'}")
    print(f"   Animations: {'✅ PASS' if animation_success else '❌ FAIL'}")
    
    print("\n💡 Check your Unity application to see if audio/animations were received.")
    print("   If tests pass but Unity doesn't respond, check Unity console for errors.")
