"""
GPT-SoVITS v2Pro Streaming Inference Test
Tests streaming audio generation with the newer v2Pro models.
"""

import os
import sys
import numpy as np
import soundfile as sf
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add GPT-SoVITS to path if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "GPT_SoVITS"))

def test_v2pro_inference():
    """Test streaming inference with v2Pro models."""
    print("="*60)
    print("GPT-SoVITS v2Pro Streaming Inference Test")
    print("="*60)
    
    # Import after path is set
    try:
        from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
    except ImportError:
        print("Error: Could not import GPT_SoVITS. Installing from pip...")
        os.system("pip install GPT-SoVITS-Fast-Inference")
        from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
    
    # Configuration
    config_path = os.getenv("GPT_SOVITS_CONFIG_PATH")
    t2s_ckpt = os.getenv("GPT_SOVITS_T2S_CKPT")
    vits_ckpt = os.getenv("GPT_SOVITS_VITS_CKPT")
    ref_audio = os.getenv("GPT_SOVITS_REF_AUDIO")
    prompt_text = os.getenv("GPT_SOVITS_PROMPT_TEXT")
    
    print(f"\nConfiguration:")
    print(f"  Config: {config_path}")
    print(f"  T2S Model: {t2s_ckpt}")
    print(f"  VITS Model: {vits_ckpt}")
    print(f"  Reference Audio: {ref_audio}")
    print(f"  Prompt Text: {prompt_text}")
    
    # Initialize TTS
    print("\n[1/4] Loading configuration...")
    cfg = TTS_Config(config_path)
    # Override config to ensure v2ProPlus settings
    cfg.device = "cpu"  # Use CPU for compatibility
    cfg.is_half = False  # Disable half precision
    cfg.version = "v2ProPlus"  # Set version explicitly
    
    print("[2/4] Initializing TTS pipeline...")
    tts = TTS(cfg)
    
    print("[3/4] Loading T2S weights...")
    tts.init_t2s_weights(t2s_ckpt)
    
    print("[4/4] Loading VITS weights...")
    tts.init_vits_weights(vits_ckpt)
    
    print("\n✓ All models loaded successfully!")
    
    # Test text
    test_text = "Hello! My name is Mitsuha. I am an artificial intelligence created by my master, Danu Kim!"
    
    print(f"\n{'='*60}")
    print("Generating Speech (Streaming Mode)")
    print(f"{'='*60}")
    print(f"Text: {test_text}")
    
    # Inference parameters
    params = {
        "text": test_text,
        "text_lang": "en",
        "ref_audio_path": ref_audio,
        "prompt_text": prompt_text,
        "prompt_lang": "en",
        "top_k": 5,
        "top_p": 1.0,
        "temperature": 1.0,
        "text_split_method": "cut5",
        "batch_size": 1,
        "speed_factor": 1.0,
        "split_bucket": True,
        "return_fragment": True,  # Enable streaming
        "fragment_interval": 0.3,
        "use_ge": False,  # Disable global embeddings to avoid dimension mismatch
        "ge_path": None,  # Explicitly set no global embedding file
    }
    
    print("\nStreaming audio generation...")
    
    # Collect all audio fragments
    all_audio = []
    sample_rate = None
    fragment_count = 0
    
    try:
        # Get the generator
        generator = tts.run(params)
        
        # Stream and collect fragments
        for sr, audio_data in generator:
            fragment_count += 1
            sample_rate = sr
            all_audio.append(audio_data)
            
            # Print progress
            audio_duration = len(audio_data) / sr
            print(f"  Fragment {fragment_count}: {len(audio_data)} samples ({audio_duration:.2f}s)")
        
        if all_audio:
            # Concatenate all fragments
            full_audio = np.concatenate(all_audio)
            
            print(f"\n✓ Generated {fragment_count} fragments")
            print(f"  Total samples: {len(full_audio)}")
            print(f"  Sample rate: {sample_rate} Hz")
            print(f"  Total duration: {len(full_audio)/sample_rate:.2f} seconds")
            
            # Save the output
            output_file = "test_v2pro_output.wav"
            sf.write(output_file, full_audio, sample_rate)
            print(f"\n✓ Audio saved to: {output_file}")
            
            return True
        else:
            print("\n❌ No audio fragments generated!")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_non_streaming():
    """Test non-streaming inference for comparison."""
    print("\n" + "="*60)
    print("GPT-SoVITS v2Pro Non-Streaming Test")
    print("="*60)
    
    from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
    
    # Configuration
    config_path = os.getenv("GPT_SOVITS_CONFIG_PATH")
    t2s_ckpt = os.getenv("GPT_SOVITS_T2S_CKPT")
    vits_ckpt = os.getenv("GPT_SOVITS_VITS_CKPT")
    ref_audio = os.getenv("GPT_SOVITS_REF_AUDIO")
    prompt_text = os.getenv("GPT_SOVITS_PROMPT_TEXT")
    
    # Initialize
    cfg = TTS_Config(config_path)
    # Override config to ensure v2ProPlus settings
    cfg.device = "cpu"  # Use CPU for compatibility
    cfg.is_half = False  # Disable half precision
    cfg.version = "v2ProPlus"  # Set version explicitly
    tts = TTS(cfg)
    tts.init_t2s_weights(t2s_ckpt)
    tts.init_vits_weights(vits_ckpt)
    
    # Test text
    test_text = "This is a non-streaming test."
    
    print(f"Text: {test_text}")
    
    # Non-streaming parameters
    params = {
        "text": test_text,
        "text_lang": "en",
        "ref_audio_path": ref_audio,
        "prompt_text": prompt_text,
        "prompt_lang": "en",
        "return_fragment": False,  # Disable streaming
        "use_ge": False,  # Disable global embeddings to avoid dimension mismatch
        "ge_path": None,  # Explicitly set no global embedding file
    }
    
    print("\nGenerating non-streaming audio...")
    
    try:
        generator = tts.run(params)
        sr, audio_data = next(generator)
        
        print(f"✓ Generated audio: {len(audio_data)} samples at {sr} Hz")
        print(f"  Duration: {len(audio_data)/sr:.2f} seconds")
        
        # Save
        sf.write("test_v2pro_nonstreaming.wav", audio_data, sr)
        print(f"✓ Saved to: test_v2pro_nonstreaming.wav")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nStarting GPT-SoVITS v2Pro Tests...\n")
    
    # Test streaming
    streaming_success = test_v2pro_inference()
    
    # Test non-streaming
    nonstreaming_success = test_non_streaming()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Streaming mode: {'✓ PASSED' if streaming_success else '❌ FAILED'}")
    print(f"Non-streaming mode: {'✓ PASSED' if nonstreaming_success else '❌ FAILED'}")
    print("="*60)
    
    if streaming_success and nonstreaming_success:
        print("\n✓ All tests passed! v2Pro models are working correctly.")
    else:
        print("\n⚠ Some tests failed. Check the error messages above.")
