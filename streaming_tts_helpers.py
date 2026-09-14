"""
Streaming TTS Helper Functions for Miko AI Assistant.
Handles concurrent sentence boundary detection, TTS generation worker, and audio queueing.
"""

import os
import queue
import re
import sys
from contextlib import contextmanager

import numpy as np


@contextmanager
def suppress_stdout_stderr():
    """Context manager to suppress stdout and stderr output."""
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = devnull
            sys.stderr = devnull
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


def detect_sentence_boundary(text: str) -> bool:
    """Check if text ends with a sentence terminator."""
    stripped = text.rstrip()
    return stripped.endswith((".", "!", "?"))


def clean_sentence_for_tts(sentence: str) -> str:
    """Clean sentence for TTS by removing emotion tags and other artifacts."""
    cleaned = sentence.strip()
    if "M.I.T.S.U.H.A." in cleaned:
        cleaned = cleaned.replace("M.I.T.S.U.H.A.", "Miko")
    if "Mitsuha" in cleaned:
        cleaned = cleaned.replace("Mitsuha", "Miko")
    cleaned = re.sub(r"\(.*?\)", "", cleaned)
    cleaned = " ".join(cleaned.split())
    return cleaned


def tts_worker(tts_queue, audio_queue, tts_engine, ref_audio, prompt_text, collected_fragments):
    """Background worker that processes TTS queue and generates audio."""
    while True:
        try:
            sentence = tts_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        if sentence is None:
            return

        if not sentence.strip():
            continue

        try:
            gen = tts_engine.generate(
                ref_audio_path=ref_audio,
                ref_text=prompt_text,
                ref_language="英文",
                target_text=sentence,
                target_language="英文",
                top_k=5,
                top_p=1.0,
                temperature=1.0,
                speed=1.0,
                stream=True,
            )
            for _sr, fragment in gen:
                if fragment.dtype != np.float32:
                    fragment = fragment.astype(np.float32)
                if collected_fragments is not None:
                    collected_fragments.append(fragment)
                audio_queue.put(fragment)
        except Exception:
            pass
