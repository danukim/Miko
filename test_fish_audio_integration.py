"""
Unit and integration tests for Fish Audio S2.1 Pro TTS pipeline and launcher.
"""

import io
import os
import queue
import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import soundfile as sf

from fish_audio_helpers import (
    FishAudioEngine,
    clean_sentence_for_tts,
    detect_sentence_boundary,
    fish_audio_tts_worker,
    fish_audio_realtime_worker,
    FlushEvent,
)


class TestFishAudioHelpers(unittest.TestCase):
    def test_sentence_boundary(self):
        self.assertTrue(detect_sentence_boundary("Hello world."))
        self.assertTrue(detect_sentence_boundary("Are you ready?"))
        self.assertTrue(detect_sentence_boundary("Let's go!"))
        self.assertFalse(detect_sentence_boundary("Incomplete sentence"))
        self.assertFalse(detect_sentence_boundary("Not done yet"))

    def test_clean_sentence(self):
        cleaned = clean_sentence_for_tts("M.I.T.S.U.H.A. is happy! (wave)")
        self.assertEqual(cleaned, "Miko is happy!")

        cleaned2 = clean_sentence_for_tts("Mitsuha says yes (thumbs-up) (clap)")
        self.assertEqual(cleaned2, "Miko says yes")

    def test_engine_initialization_defaults(self):
        engine = FishAudioEngine(api_key="test_key_123")
        self.assertEqual(engine.model, "s2.1-pro-free")
        self.assertEqual(engine.target_sample_rate, 44100)
        self.assertEqual(engine.chunk_size, 2048)
        self.assertTrue(engine.is_configured())

    def test_engine_unconfigured(self):
        engine = FishAudioEngine(api_key=None, client=None)
        # Without FISH_API_KEY in env
        with patch.dict(os.environ, {}, clear=True):
            engine = FishAudioEngine(api_key=None, client=None)
            self.assertFalse(engine.is_configured())
            with self.assertRaises(ValueError):
                engine.synthesize_sentence("Hello")

    def test_engine_synthesize_with_mock_client(self):
        # Create a mock WAV bytes stream (44100Hz, 1 second, float32)
        mock_audio = np.sin(np.linspace(0, 440 * 2 * np.pi, 44100, dtype=np.float32)) * 0.5
        wav_buf = io.BytesIO()
        sf.write(wav_buf, mock_audio, 44100, format="WAV", subtype="FLOAT")
        wav_bytes = wav_buf.getvalue()

        mock_client = MagicMock()
        mock_client.tts.convert.return_value = wav_bytes

        engine = FishAudioEngine(
            api_key="mock_key",
            model="s2.1-pro-free",
            target_sample_rate=44100,
            client=mock_client,
        )

        audio_data, sr = engine.synthesize_sentence("Hello world.")
        self.assertEqual(sr, 44100)
        self.assertIsInstance(audio_data, np.ndarray)
        self.assertEqual(audio_data.dtype, np.float32)
        self.assertEqual(len(audio_data), 44100)
        self.assertTrue(np.all(audio_data >= -1.0) and np.all(audio_data <= 1.0))
        mock_client.tts.convert.assert_called_once()

    def test_engine_custom_model_id(self):
        mock_client = MagicMock()
        mock_audio = np.zeros(2048, dtype=np.float32)
        wav_buf = io.BytesIO()
        sf.write(wav_buf, mock_audio, 44100, format="WAV", subtype="FLOAT")
        mock_client.tts.convert.return_value = wav_buf.getvalue()

        custom_id = "344d8217dee64170a58b6a0cf80d0e95"
        engine = FishAudioEngine(
            api_key="mock",
            model="s2.1-pro-free",
            reference_id=custom_id,
            ref_audio_path="Kokomi_0.wav",  # Should be ignored because reference_id is provided
            client=mock_client,
        )
        self.assertEqual(engine.reference_id, custom_id)
        self.assertIsNone(engine.references)  # Zero shot must be disabled

        engine.synthesize_sentence("Testing persistent model.")
        mock_client.tts.convert.assert_called_with(
            text="Testing persistent model.",
            format="wav",
            model="s2.1-pro-free",
            reference_id=custom_id,
            references=None,
            latency="balanced",
        )

    def test_insufficient_credit_error_handling(self):
        mock_client = MagicMock()
        mock_client.tts.convert.side_effect = Exception("HTTP 402: Insufficient API credit")

        engine = FishAudioEngine(api_key="mock", client=mock_client)
        with self.assertRaises(RuntimeError) as ctx:
            engine.synthesize_sentence("Hello")
        self.assertIn("Insufficient developer API credit", str(ctx.exception))


    def test_engine_synthesize_resampling(self):
        # Generate 22050Hz audio, engine target is 44100Hz
        mock_audio = np.sin(np.linspace(0, 440 * 2 * np.pi, 22050, dtype=np.float32)) * 0.5
        wav_buf = io.BytesIO()
        sf.write(wav_buf, mock_audio, 22050, format="WAV", subtype="FLOAT")
        wav_bytes = wav_buf.getvalue()

        mock_client = MagicMock()
        mock_client.tts.convert.return_value = wav_bytes

        engine = FishAudioEngine(
            api_key="mock_key",
            model="s2.1-pro",
            target_sample_rate=44100,
            client=mock_client,
        )

        audio_data, sr = engine.synthesize_sentence("Test resampling.")
        self.assertEqual(sr, 44100)
        self.assertEqual(len(audio_data), 44100)

    def test_chunk_audio(self):
        engine = FishAudioEngine(api_key="mock", chunk_size=1000)
        data = np.zeros(2500, dtype=np.float32)
        chunks = list(engine.chunk_audio(data))
        self.assertEqual(len(chunks), 3)
        self.assertEqual(len(chunks[0]), 1000)
        self.assertEqual(len(chunks[1]), 1000)
        self.assertEqual(len(chunks[2]), 500)

    def test_tts_worker_pipeline(self):
        # Create mock audio
        mock_audio = np.ones(4096, dtype=np.float32) * 0.2
        wav_buf = io.BytesIO()
        sf.write(wav_buf, mock_audio, 44100, format="WAV", subtype="FLOAT")
        wav_bytes = wav_buf.getvalue()

        mock_client = MagicMock()
        mock_client.tts.convert.return_value = wav_bytes

        engine = FishAudioEngine(
            api_key="mock",
            model="s2.1-pro",
            target_sample_rate=44100,
            chunk_size=2048,
            client=mock_client,
        )

        tts_queue = queue.Queue()
        audio_queue = queue.Queue()
        collected = []

        # Enqueue a sentence and a shutdown signal
        tts_queue.put("Hello from test.")
        tts_queue.put(None)

        fish_audio_tts_worker(tts_queue, audio_queue, engine, collected_fragments=collected)

        # Worker should have processed 1 sentence
        self.assertEqual(len(collected), 1)
        self.assertEqual(len(collected[0]), 4096)

        # By default, full sentence audio fragment is queued directly (no slicing)
        fragments = []
        while not audio_queue.empty():
            fragments.append(audio_queue.get_nowait())

        self.assertEqual(len(fragments), 1)
        self.assertEqual(len(fragments[0]), 4096)

        # Test chunk_stream=True mode
        tts_queue.put("Chunked test.")
        tts_queue.put(None)
        fish_audio_tts_worker(tts_queue, audio_queue, engine, chunk_stream=True)
        chunks = []
        while not audio_queue.empty():
            chunks.append(audio_queue.get_nowait())
        self.assertEqual(len(chunks), 2)
        self.assertEqual(len(chunks[0]), 2048)
        self.assertEqual(len(chunks[1]), 2048)



class TestFishAudioRealtimeStreaming(unittest.TestCase):
    def test_stream_realtime_pcm(self):
        # Create mock 16-bit PCM data (1000 samples of int16 zeros)
        int16_samples = np.zeros(1000, dtype=np.int16)
        raw_pcm = int16_samples.tobytes()

        mock_client = MagicMock()
        mock_client.tts.stream_websocket.return_value = [raw_pcm, raw_pcm]

        engine = FishAudioEngine(
            api_key="mock_key",
            model="s2.1-pro-free",
            target_sample_rate=44100,
            client=mock_client,
        )

        def text_gen():
            yield "Hello "
            yield "world!"

        # When min_chunk_seconds=0, yields raw incoming chunks
        chunks = list(engine.stream_realtime(text_gen(), format="pcm", min_chunk_seconds=0))
        self.assertEqual(len(chunks), 2)
        self.assertIsInstance(chunks[0], np.ndarray)
        self.assertEqual(chunks[0].dtype, np.float32)
        self.assertEqual(len(chunks[0]), 1000)

        # When min_chunk_seconds > 0, aggregates chunks into smooth blocks
        aggregated = list(engine.stream_realtime(text_gen(), format="pcm", min_chunk_seconds=0.5))
        self.assertEqual(len(aggregated), 1)
        self.assertEqual(len(aggregated[0]), 2000)

    def test_fish_audio_realtime_worker_filters_motion_preserves_fish_tags(self):
        captured_stream_tokens = []

        def mock_stream_ws(text_stream, **kwargs):
            for token in text_stream:
                captured_stream_tokens.append(token)
            int16_data = np.zeros(500, dtype=np.int16).tobytes()
            yield int16_data

        mock_client = MagicMock()
        mock_client.tts.stream_websocket.side_effect = mock_stream_ws

        engine = FishAudioEngine(
            api_key="mock_key",
            model="s2.1-pro-free",
            client=mock_client,
        )

        token_queue = queue.Queue()
        audio_queue = queue.Queue()
        collected = []

        # Send tokens containing Unity motions, M.I.T.S.U.H.A., and Fish Audio [excited] [giggle] tags
        tokens = [
            "[excited] ",
            "Hi there! ",
            "[giggle] ",
            "I am ",
            "M.I.T.S.U.H.A. ",
            "(wave) ",
            "How are ",
            "you? ",
            "(nodding)",
        ]
        for t in tokens:
            token_queue.put(t)
        token_queue.put(None)

        fish_audio_realtime_worker(token_queue, audio_queue, engine, collected_fragments=collected)

        str_tokens = [t for t in captured_stream_tokens if isinstance(t, str)]
        flush_tokens = [t for t in captured_stream_tokens if FlushEvent is not None and isinstance(t, FlushEvent)]

        full_sent_to_fish = "".join(str_tokens)

        # FlushEvent is not sent to avoid duplicating the final synthesized chunk
        self.assertEqual(len(flush_tokens), 0)

        # Motion tags in parentheses must be filtered out
        self.assertNotIn("(wave)", full_sent_to_fish)
        self.assertNotIn("(nodding)", full_sent_to_fish)

        # Fish Audio tags in square brackets must be preserved
        self.assertIn("[excited]", full_sent_to_fish)
        self.assertIn("[giggle]", full_sent_to_fish)

        # M.I.T.S.U.H.A. converted to Miko
        self.assertIn("Miko", full_sent_to_fish)
        self.assertNotIn("M.I.T.S.U.H.A.", full_sent_to_fish)

        # Audio queue received data followed by None
        self.assertEqual(len(collected), 1)
        audio_out = []
        while not audio_queue.empty():
            audio_out.append(audio_queue.get_nowait())
        self.assertEqual(len(audio_out), 2)  # 1 chunk + None sentinel
        self.assertIsInstance(audio_out[0], np.ndarray)
        self.assertIsNone(audio_out[1])

    def test_fish_audio_realtime_worker_filters_bracketed_gestures_and_converts_voice_tags(self):
        mock_client = MagicMock()
        captured_stream_tokens = []

        def mock_stream_ws(text_iterator, **kwargs):
            for item in text_iterator:
                captured_stream_tokens.append(item)
            chunk = np.zeros(1024, dtype=np.float32).tobytes()
            yield chunk

        mock_client.tts.stream_websocket.side_effect = mock_stream_ws

        engine = FishAudioEngine(
            api_key="mock_key",
            model="s2.1-pro-free",
            client=mock_client,
        )

        token_queue = queue.Queue()
        audio_queue = queue.Queue()
        collected = []

        # Send tokens containing bracketed gesture [wave], parenthesized voice tag (whisper), and normal text
        tokens = [
            "(whisper) ",
            "I have a secret! ",
            "[wave]",
        ]
        for t in tokens:
            token_queue.put(t)
        token_queue.put(None)

        fish_audio_realtime_worker(token_queue, audio_queue, engine, collected_fragments=collected)

        full_sent = "".join([t for t in captured_stream_tokens if isinstance(t, str)])
        # [wave] must be stripped
        self.assertNotIn("wave", full_sent)
        self.assertNotIn("[wave]", full_sent)
        # (whisper) must be converted to [whisper]
        self.assertIn("[whisper]", full_sent)
        self.assertIn("I have a secret!", full_sent)

    def test_fish_audio_realtime_worker_empty_stream(self):
        mock_client = MagicMock()
        engine = FishAudioEngine(
            api_key="mock_key",
            model="s2.1-pro-free",
            client=mock_client,
        )

        token_queue = queue.Queue()
        audio_queue = queue.Queue()

        # Send only empty/whitespace tokens
        token_queue.put("   ")
        token_queue.put("")
        token_queue.put(None)

        fish_audio_realtime_worker(token_queue, audio_queue, engine)

        # Should NOT call WebSocket
        mock_client.tts.stream_websocket.assert_not_called()

        # Audio queue should just get None sentinel
        self.assertEqual(audio_queue.get_nowait(), None)

    def test_smart_buffering_and_trailing_tag_suppression(self):
        mock_client = MagicMock()
        captured_chunks = []

        def mock_stream_ws(text_iterator, **kwargs):
            for item in text_iterator:
                captured_chunks.append(item)
            chunk = np.zeros(500, dtype=np.int16).tobytes()
            yield chunk

        mock_client.tts.stream_websocket.side_effect = mock_stream_ws

        engine = FishAudioEngine(
            api_key="mock_key",
            model="s2.1-pro-free",
            client=mock_client,
        )

        token_queue = queue.Queue()
        audio_queue = queue.Queue()
        collected = []

        tokens = [
            "Glad ", "to ", "hear ", "that! ",
            "So, ", "what's ", "been ", "keeping ", "you ", "busy ", "lately? ",
            "[curious]"
        ]
        for t in tokens:
            token_queue.put(t)
        token_queue.put(None)

        fish_audio_realtime_worker(token_queue, audio_queue, engine, collected_fragments=collected)

        # Chunks should be buffered at sentence boundaries
        self.assertTrue(len(captured_chunks) >= 2)
        full_text = "".join(captured_chunks)
        self.assertIn("Glad to hear that!", full_text)
        self.assertIn("what's been keeping you busy lately?", full_text)
        # Trailing tag [curious] with no words after it must be suppressed to avoid audio hallucination
        self.assertNotIn("[curious]", full_text)

    def test_realtime_worker_fallback_on_websocket_error(self):
        mock_client = MagicMock()
        # Simulate WebSocket throwing an error
        mock_client.tts.stream_websocket.side_effect = Exception("WebSocket stream ended with error")

        engine = FishAudioEngine(
            api_key="mock_key",
            model="s2.1-pro-free",
            client=mock_client,
        )

        # Mock synthesize_sentence on engine
        fallback_audio = np.ones(1024, dtype=np.float32)
        engine.synthesize_sentence = MagicMock(return_value=(fallback_audio, 44100))

        token_queue = queue.Queue()
        audio_queue = queue.Queue()
        collected = []

        token_queue.put("Hello ")
        token_queue.put("world! ")
        token_queue.put(None)

        fish_audio_realtime_worker(token_queue, audio_queue, engine, collected_fragments=collected)

        # synthesize_sentence should have been called as fallback
        engine.synthesize_sentence.assert_called_once()
        # Audio queue should have received the fallback audio followed by None sentinel
        self.assertEqual(len(collected), 1)
        self.assertTrue(np.array_equal(collected[0], fallback_audio))

    def test_japanese_sentence_terminators(self):
        self.assertTrue(detect_sentence_boundary("こんにちは！"))
        self.assertTrue(detect_sentence_boundary("元気ですか？"))
        self.assertTrue(detect_sentence_boundary("いい天気ですね。"))
        self.assertFalse(detect_sentence_boundary("こんにちは"))


class TestLauncherAndScripts(unittest.TestCase):
    def test_launcher_bat_exists_and_configured(self):
        bat_path = os.path.join(os.path.dirname(__file__), "start_fishaudio.bat")
        self.assertTrue(os.path.exists(bat_path))
        with open(bat_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Miko_FishAudio.py", content)
        self.assertIn("app.py", content)
        self.assertIn("ollama", content)
        self.assertIn("venv\\Scripts\\python.exe", content)

    def test_miko_fishaudio_script_exists(self):
        py_path = os.path.join(os.path.dirname(__file__), "Miko_FishAudio.py")
        self.assertTrue(os.path.exists(py_path))
        with open(py_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("FishAudioEngine", content)
        self.assertIn("fish_audio_tts_worker", content)
        self.assertIn("s2.1-pro", content)


if __name__ == "__main__":
    unittest.main()
