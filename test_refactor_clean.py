"""
Test suite to verify core functionality across Miko modules.
Used as the regression baseline during /refactor-clean.
"""

import unittest
from unittest.mock import MagicMock
from datetime import datetime


class TestMemoryEnhanced(unittest.TestCase):
    def setUp(self):
        from memory_enhanced import ImportanceScorer, EnhancedMemory
        self.scorer = ImportanceScorer()
        self.memory = EnhancedMemory(base_memory=MagicMock(), conversation_file="conversation.jsonl")

    def test_importance_scorer_high_importance(self):
        score, tags = self.scorer.score_message("user", "my name is Danu and I live in Tokyo")
        self.assertGreaterEqual(score, 0.7)
        self.assertIn("personal_fact", tags)

    def test_importance_scorer_low_importance(self):
        score, tags = self.scorer.score_message("user", "okay cool yeah sure")
        self.assertLess(score, 0.6)

    def test_temporal_factor(self):
        now = datetime.now()
        factor = self.memory.calculate_temporal_factor(now, now)
        self.assertAlmostEqual(factor, 1.0, places=1)


class TestAudioStreamer(unittest.TestCase):
    def test_audio_streamer_init(self):
        from audio_streamer import AudioStreamer, DualAudioPlayer, create_miko_audio_handler, create_mitsuha_audio_handler
        streamer = AudioStreamer("http://localhost:8000")
        self.assertEqual(streamer.server_url, "http://localhost:8000")
        self.assertFalse(streamer.is_streaming)

        player = DualAudioPlayer("http://localhost:8000", local_volume=0.0)
        self.assertEqual(player.local_volume, 0.0)

        handler = create_miko_audio_handler("http://localhost:8000", 0.0)
        self.assertIsNotNone(handler)

        legacy_handler = create_mitsuha_audio_handler("http://localhost:8000", 0.0)
        self.assertIsNotNone(legacy_handler)


class TestAppServer(unittest.TestCase):
    def test_file_upload_handler_attributes(self):
        from app import FileUploadHandler
        self.assertTrue(hasattr(FileUploadHandler, "broadcast_face_position"))
        self.assertTrue(hasattr(FileUploadHandler, "broadcast_animation_command"))
        self.assertTrue(hasattr(FileUploadHandler, "audio_clients"))


class TestMikoCore(unittest.TestCase):
    def test_formatting_functions(self):
        import re
        import MITSUHAVR_Ollama as miko
        miko.re = re
        self.assertTrue(hasattr(miko, "kawaii_gradient_text"))
        self.assertTrue(hasattr(miko, "gradient_text"))
        self.assertTrue(hasattr(miko, "strip_ansi_codes"))
        self.assertTrue(hasattr(miko, "typewriter_effect"))

        res = miko.kawaii_gradient_text("Test", "#FF0000", "#00FF00")
        stripped = miko.strip_ansi_codes(res)
        self.assertEqual(stripped, "Test")


class TestStreamingTTSHelpers(unittest.TestCase):
    def test_detect_sentence_boundary(self):
        import streaming_tts_helpers as helpers
        self.assertTrue(helpers.detect_sentence_boundary("Hello world."))
        self.assertTrue(helpers.detect_sentence_boundary("How are you?"))
        self.assertTrue(helpers.detect_sentence_boundary("Amazing!"))
        self.assertFalse(helpers.detect_sentence_boundary("Incomplete sentence"))

    def test_clean_sentence_for_tts(self):
        import streaming_tts_helpers as helpers
        cleaned = helpers.clean_sentence_for_tts("M.I.T.S.U.H.A. is ready! (wave)")
        self.assertEqual(cleaned, "Miko is ready!")
        cleaned2 = helpers.clean_sentence_for_tts("Hello Mitsuha (thumbs-up)")
        self.assertEqual(cleaned2, "Hello Miko")


if __name__ == "__main__":
    unittest.main()
