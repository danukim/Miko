"""
Audio streaming module for MITSUHA AI Assistant
Handles real-time audio streaming to Unity desktop avatar
"""

import requests
import base64
import json
import numpy as np
import threading
import time
from typing import Optional, Callable
import queue

class AudioStreamer:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.sample_rate = 22050
        self.is_streaming = False
        self.session = requests.Session()
        
    def start_stream(self, sample_rate: int = 22050):
        """Signal the start of a new audio stream"""
        self.sample_rate = sample_rate
        self.is_streaming = True
        
        # print(f"🎵 Starting audio stream to: {self.server_url}")
        
        try:
            payload = {
                'type': 'audio_start',
                'sample_rate': sample_rate
            }
            # print(f"🎵 Sending payload: {payload}")
            
            response = self.session.post(
                self.server_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            # print(f"🎵 Server response: {response.status_code} - {response.text}")
            response.raise_for_status()
            # print(f"✨ Audio stream started (Sample rate: {sample_rate}Hz)")
        except Exception as e:
            print(f"❌ Failed to start audio stream: {e}")
    
    def stream_chunk(self, audio_data: np.ndarray):
        """Stream a chunk of audio data to Unity"""
        if not self.is_streaming:
            # print("⚠️ Audio stream not started. Call start_stream() first.")
            return
            
        try:
            # Convert numpy array to bytes
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            audio_bytes = audio_data.tobytes()
            
            payload = {
                'type': 'audio_chunk',
                'audio_data': base64.b64encode(audio_bytes).decode('utf-8'),
                'sample_rate': self.sample_rate
            }
            
            # Send to server
            response = self.session.post(
                self.server_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=1
            )
            # print(f"🎵 Chunk response: {response.status_code}")
            response.raise_for_status()
            
        except Exception as e:
            print(f"❌ Failed to stream audio chunk: {e}")
    
    def send_animation_command(self, animation_name: str):
        """Send animation command to Unity"""
        try:
            payload = {
                'type': 'animation_command',
                'animation': animation_name
            }
            # print(f"🎭 Sending animation command: {animation_name}")
            
            response = self.session.post(
                self.server_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            # print(f"🎭 Animation response: {response.status_code}")
            response.raise_for_status()
            # print(f"✨ Animation command sent: {animation_name}")
        except Exception as e:
            print(f"❌ Failed to send animation command: {e}")
    
    def end_stream(self):
        """Signal the end of the audio stream"""
        if not self.is_streaming:
            return
            
        self.is_streaming = False
        
        try:
            payload = {'type': 'audio_end'}
            # print(f"🎵 Ending stream with payload: {payload}")
            
            response = self.session.post(
                self.server_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            # print(f"🎵 End response: {response.status_code} - {response.text}")
            response.raise_for_status()
            # print("✨ Audio stream ended")
        except Exception as e:
            print(f"❌ Failed to end audio stream: {e}")

class DualAudioPlayer:
    """
    Plays audio both locally (muted for timing) and streams to Unity
    Maintains perfect synchronization between local playback and Unity
    """
    
    def __init__(self, streamer: AudioStreamer, local_volume: float = 0.0):
        self.streamer = streamer
        self.local_volume = local_volume
        self.audio_queue = queue.Queue()
        self.playback_thread = None
        self.stop_event = threading.Event()
        
        # Import sounddevice locally to avoid conflicts
        try:
            import sounddevice as sd
            self.sd = sd
            self.sd_available = True
        except ImportError:
            # print("⚠️ sounddevice not available. Unity streaming only.")
            self.sd_available = False
    
    def send_animation(self, animation_name: str):
        """Send animation command to Unity"""
        self.streamer.send_animation_command(animation_name)
    
    def start_playback(self, sample_rate: int = 22050):
        """Start dual audio playback (local + Unity streaming)"""
        self.stop_event.clear()
        self.streamer.start_stream(sample_rate)
        
        if self.sd_available:
            self.playback_thread = threading.Thread(
                target=self._playback_worker,
                args=(sample_rate,),
                daemon=True
            )
            self.playback_thread.start()
    
    def add_audio_chunk(self, audio_data: np.ndarray):
        """Add audio chunk to be played locally and streamed to Unity"""
        # Stream to Unity immediately
        self.streamer.stream_chunk(audio_data)
        
        # Queue for local playback
        if self.sd_available:
            self.audio_queue.put(audio_data)
    
    def stop_playback(self):
        """Stop playback and streaming"""
        self.stop_event.set()
        self.streamer.end_stream()
        
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=2)
    
    def _playback_worker(self, sample_rate: int):
        """Worker thread for local audio playback"""
        if not self.sd_available:
            return
            
        try:
            # Configure sounddevice
            self.sd.default.samplerate = sample_rate
            self.sd.default.channels = 1
            
            with self.sd.OutputStream(dtype='float32') as stream:
                while not self.stop_event.is_set():
                    try:
                        # Get audio chunk with timeout
                        audio_chunk = self.audio_queue.get(timeout=0.1)
                        
                        # Apply volume (0.0 for muted timing track)
                        audio_chunk = audio_chunk * self.local_volume
                        
                        # Play locally
                        stream.write(audio_chunk)
                        
                    except queue.Empty:
                        continue
                    except Exception as e:
                        print(f"❌ Local playback error: {e}")
                        break
                        
        except Exception as e:
            print(f"❌ Failed to initialize local audio playback: {e}")

# Example integration function for MITSUHA
def create_mitsuha_audio_handler(server_url: str = "http://localhost:8000", 
                                local_volume: float = 0.0):
    """
    Create an audio handler for MITSUHA that streams to Unity
    
    Args:
        server_url: URL of the app.py server
        local_volume: Volume for local playback (0.0 = muted for timing only)
    
    Returns:
        DualAudioPlayer instance ready for use
    """
    streamer = AudioStreamer(server_url)
    player = DualAudioPlayer(streamer, local_volume)
    
    return player

# Example usage in MITSUHA's audio_playback_thread function
def example_mitsuha_integration():
    """
    Example of how to integrate this with MITSUHA's existing audio system
    """
    
    # Replace the existing audio_playback_thread function with this:
    def audio_playback_thread_with_streaming(audio_queue: queue.Queue, sample_rate: int):
        """
        Enhanced audio playback thread that streams to Unity while playing locally
        """
        # Create dual audio player
        dual_player = create_mitsuha_audio_handler(
            server_url="http://localhost:8000",
            local_volume=0.0  # Muted for timing only
        )
        
        dual_player.start_playback(sample_rate)
        
        try:
            while True:
                try:
                    # Get audio fragment from TTS generation
                    audio_fragment = audio_queue.get(timeout=1.0)
                    
                    if audio_fragment is None:  # Shutdown signal
                        break
                    
                    # Play locally (muted) and stream to Unity
                    dual_player.add_audio_chunk(audio_fragment)
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"❌ Audio playback error: {e}")
                    break
                    
        finally:
            dual_player.stop_playback()
    
    return audio_playback_thread_with_streaming

if __name__ == "__main__":
    # Test the audio streamer
    print("🎵 Testing Audio Streamer...")
    
    streamer = AudioStreamer()
    streamer.start_stream(22050)
    
    # Generate test audio
    import numpy as np
    duration = 1.0  # 1 second
    sample_rate = 22050
    t = np.linspace(0, duration, int(sample_rate * duration))
    test_audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)  # 440Hz sine wave
    
    # Stream in chunks
    chunk_size = 1024
    for i in range(0, len(test_audio), chunk_size):
        chunk = test_audio[i:i+chunk_size]
        streamer.stream_chunk(chunk)
        time.sleep(chunk_size / sample_rate)  # Real-time playback
    
    streamer.end_stream()
    print("✨ Test completed!")
