"""
Fish Audio TTS Helper Functions for Miko AI Assistant.
Provides integration with the Fish Audio S2.1 Pro API, audio decoding,
sample rate conversion, chunk streaming, and background queue workers.
"""

import io
import os
import queue
import re
import sys
from typing import Generator, List, Optional, Tuple

import numpy as np
import soundfile as sf
from dotenv import load_dotenv

load_dotenv()

try:
    import soxr
except ImportError:
    soxr = None

from fishaudio import FishAudio
try:
    from fishaudio import FlushEvent
except ImportError:
    try:
        from fishaudio.types import FlushEvent
    except ImportError:
        FlushEvent = None
from fishaudio.types import ReferenceAudio


def detect_sentence_boundary(text: str) -> bool:
    """Check if text ends with a sentence terminator (. ! ? 。 ！ ？)."""
    stripped = text.rstrip()
    return stripped.endswith((".", "!", "?", "。", "！", "？"))


def clean_sentence_for_tts(sentence: str) -> str:
    """Clean sentence for TTS by removing motion gestures, emojis, and trailing empty tags."""
    cleaned = sentence.strip()
    if "M.I.T.S.U.H.A." in cleaned:
        cleaned = cleaned.replace("M.I.T.S.U.H.A.", "Miko")
    if "Mitsuha" in cleaned:
        cleaned = cleaned.replace("Mitsuha", "Miko")
    # Remove avatar body animations like (wave), [wave], (thumbs-up), [thumbs-up], etc.
    cleaned = re.sub(r"[\(\[][^)\]]*(?:wave|thumbs|nod|shak|clap|open:|close:)[^)\]]*[\)\]]", "", cleaned, flags=re.IGNORECASE)
    # Remove any remaining parentheticals
    cleaned = re.sub(r"\(.*?\)", "", cleaned)
    # Remove surrogate emojis
    cleaned = re.sub(r"[\U00010000-\U0010ffff]", "", cleaned)
    # Strip trailing emotion tag if no words follow it to prevent Fish Audio hallucination
    cleaned = re.sub(r"\s*\[[a-zA-Z\s]+\]\s*$", "", cleaned)
    # Collapse multiple whitespaces
    cleaned = " ".join(cleaned.split())
    return cleaned


class FishAudioEngine:
    """
    Wrapper for Fish Audio text-to-speech engine.
    Handles authentication, voice references, synthesis, audio decoding, and chunking.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        reference_id: Optional[str] = None,
        ref_audio_path: Optional[str] = None,
        ref_prompt_text: Optional[str] = None,
        target_sample_rate: int = 44100,
        chunk_size: int = 2048,
        client: Optional[FishAudio] = None,
    ):
        self.api_key = api_key or os.getenv("FISH_API_KEY")
        self.model = model or os.getenv("FISH_AUDIO_MODEL", "s2.1-pro-free")
        self.reference_id = reference_id or os.getenv("FISH_AUDIO_REFERENCE_ID") or os.getenv("FISH_AUDIO_VOICE_ID")
        self.target_sample_rate = target_sample_rate
        self.chunk_size = chunk_size

        # Instant voice cloning reference
        self.references: Optional[List[ReferenceAudio]] = None
        if not self.reference_id:
            audio_path = ref_audio_path or os.getenv("FISH_AUDIO_REF_AUDIO") or os.getenv("GPT_SOVITS_REF_AUDIO")
            prompt_text = ref_prompt_text or os.getenv("FISH_AUDIO_PROMPT_TEXT") or os.getenv("GPT_SOVITS_PROMPT_TEXT")
            if audio_path and os.path.exists(audio_path) and prompt_text:
                try:
                    with open(audio_path, "rb") as f:
                        ref_bytes = f.read()
                    self.references = [ReferenceAudio(audio=ref_bytes, text=prompt_text)]
                except Exception as e:
                    print(f"⚠️ Warning: Could not load reference audio '{audio_path}': {e}", file=sys.stderr)

        # Initialize Fish Audio client
        if client is not None:
            self.client = client
        elif self.api_key:
            self.client = FishAudio(api_key=self.api_key)
        else:
            self.client = None

    def is_configured(self) -> bool:
        """Check if client is configured with an API key."""
        return self.client is not None

    def synthesize_sentence(self, text: str) -> Tuple[np.ndarray, int]:
        """
        Synthesize text to float32 audio samples using Fish Audio S2.1 Pro API.

        Returns:
            Tuple of (audio_numpy_float32, sample_rate)
        """
        if not self.client:
            raise ValueError("Fish Audio client is not configured. Please set FISH_API_KEY.")

        # Request audio in WAV format
        try:
            audio_bytes = self.client.tts.convert(
                text=text,
                format="wav",
                model=self.model,  # type: ignore[arg-type]
                reference_id=self.reference_id,
                references=self.references,
                latency="balanced",
            )
        except Exception as e:
            err_msg = str(e)
            if "402" in err_msg or "Insufficient API credit" in err_msg:
                raise RuntimeError(
                    "Fish Audio HTTP 402: Insufficient developer API credit! "
                    "Note: Developer API credit is separate from web platform credit. "
                    "Please visit https://fish.audio/app/developers to check or top up your API balance."
                ) from e
            if "401" in err_msg or "Unauthorized" in err_msg:
                raise RuntimeError(
                    "Fish Audio HTTP 401: Unauthorized API key! "
                    "Please verify your FISH_API_KEY in .env."
                ) from e
            raise

        with io.BytesIO(audio_bytes) as bio:
            audio_data, sr = sf.read(bio, dtype="float32")

        # Convert stereo to mono if needed
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        # Resample if sample rate doesn't match target
        if sr != self.target_sample_rate:
            if soxr is not None:
                audio_data = soxr.resample(audio_data, sr, self.target_sample_rate)
            else:
                # Basic linear interpolation fallback if soxr is missing
                old_len = len(audio_data)
                new_len = int(old_len * self.target_sample_rate / sr)
                audio_data = np.interp(
                    np.linspace(0, old_len, new_len, endpoint=False),
                    np.arange(old_len),
                    audio_data,
                ).astype(np.float32)
            sr = self.target_sample_rate

        return audio_data, sr

    def chunk_audio(self, audio_data: np.ndarray) -> Generator[np.ndarray, None, None]:
        """Slice audio array into smaller chunks for smooth real-time streaming and lip sync."""
        total_len = len(audio_data)
        for i in range(0, total_len, self.chunk_size):
            yield audio_data[i : i + self.chunk_size]

    def stream_realtime(
        self,
        text_stream,
        format: str = "pcm",
        min_chunk_seconds: float = 0.0,
    ) -> Generator[np.ndarray, None, None]:
        """
        Stream text tokens to Fish Audio via WebSocket (/v1/tts/live) and yield
        normalized float32 audio chunks in real time as they arrive.

        Args:
            text_stream: An iterable or generator yielding text tokens.
            format: Audio format requested from WebSocket ("pcm" or "wav").
            min_chunk_seconds: Minimum duration in seconds to accumulate before yielding.
                               0.0 yields chunks immediately as they arrive from WebSocket (~90-400ms TTFA).

        Yields:
            np.ndarray: Float32 normalized audio samples for each audio block.
        """
        if not self.is_configured():
            return

        min_samples = int(self.target_sample_rate * min_chunk_seconds) if min_chunk_seconds > 0 else 0
        buffer: List[np.ndarray] = []
        accum_samples = 0

        try:
            for chunk in self.client.tts.stream_websocket(
                text_stream,
                model=self.model,
                reference_id=self.reference_id,
                format=format,
                latency="balanced",
            ):
                if not chunk:
                    continue

                if format == "pcm":
                    # 16-bit signed PCM mono audio at 44100 Hz
                    audio_floats = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
                elif format == "wav":
                    with io.BytesIO(chunk) as buf:
                        audio_floats, sr = sf.read(buf, dtype="float32")
                else:
                    continue

                if self.target_sample_rate != 44100 and soxr is not None:
                    audio_floats = soxr.resample(audio_floats, 44100, self.target_sample_rate)

                if min_samples > 0:
                    buffer.append(audio_floats)
                    accum_samples += len(audio_floats)
                    if accum_samples >= min_samples:
                        combined = np.concatenate(buffer)
                        yield combined
                        buffer.clear()
                        accum_samples = 0
                else:
                    yield audio_floats

            if buffer:
                combined = np.concatenate(buffer)
                yield combined
                buffer.clear()
        except Exception as e:
            print(f"\n❌ Fish Audio WebSocket streaming error: {e}", file=sys.stderr)
            try:
                self.client = FishAudio(api_key=self.api_key)
            except Exception:
                pass
            raise


def fish_audio_tts_worker(
    tts_queue: queue.Queue,
    audio_queue: queue.Queue,
    engine: FishAudioEngine,
    collected_fragments: Optional[list] = None,
    chunk_stream: bool = False,
):
    """
    Background worker thread that receives text sentences from tts_queue,
    calls FishAudioEngine to generate audio, and puts audio fragments into audio_queue.

    NOTE: By default, full sentence audio fragments are queued directly (matching
    GPT-SoVITS streaming behavior). Unity's Voice.cs/MikoAudioReceiver handles internal
    circular buffer management in OnAudioRead. Slicing into tiny ~2048-sample (46ms)
    chunks caused network request storms over HTTP, starving Unity's buffer and
    causing chopped/stuttering audio bursts.
    """
    while True:
        try:
            sentence = tts_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        if sentence is None:  # Shutdown signal
            return

        if not sentence.strip():
            continue

        try:
            audio_data, _sr = engine.synthesize_sentence(sentence)
            if collected_fragments is not None:
                collected_fragments.append(audio_data)

            if chunk_stream:
                for chunk in engine.chunk_audio(audio_data):
                    audio_queue.put(chunk)
            else:
                audio_queue.put(audio_data)
        except Exception as e:
            print(f"\n❌ Fish Audio TTS generation error: {e}", file=sys.stderr)


def fish_audio_realtime_worker(
    token_queue: queue.Queue,
    audio_queue: queue.Queue,
    engine: FishAudioEngine,
    collected_fragments: Optional[list] = None,
    min_chars_per_flush: int = 20,
    min_chunk_seconds: float = 0.0,
):
    """
    Background worker thread that receives streaming LLM text tokens from token_queue,
    filters out Unity body motions in parentheses while preserving Fish Audio [tags],
    and feeds the tokens directly to engine.stream_realtime() via WebSocket as they generate.
    Audio chunks are yielded directly to audio_queue with minimal latency (~90-400ms TTFA).
    No FlushEvent is sent, preventing duplicated synthesis of the final chunk and eliminates choppiness.
    """
    GESTURE_TAGS = {"wave", "thumbs-up", "thumbs- up", "nodding", "shaking head", "shaking- head", "clap"}
    VOICE_TAGS = {
        "excited", "whisper", "cheerful", "curious", "pouty",
        "tender", "teasing", "sarcastic", "giggle", "chuckle",
        "sigh", "gasp", "yawn", "snicker", "short pause", "long pause",
        "happy", "sad", "laugh", "angry", "playful"
    }

    terminal_punct = {".", "!", "?", "\n", "。", "！", "？"}
    clause_punct = {",", ";", ":", "、", "…"}

    def token_filter():
        paren_buffer = ""
        in_paren = False
        bracket_buffer = ""
        in_bracket = False
        accum_text = ""

        while True:
            try:
                token = token_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if token is None:
                # End of LLM generation: cleanly terminate text stream
                break
            if not token:
                continue

            if "M.I.T.S.U.H.A." in token:
                token = token.replace("M.I.T.S.U.H.A.", "Miko")
            if "Mitsuha" in token:
                token = token.replace("Mitsuha", "Miko")

            token = re.sub(r"[\U00010000-\U0010ffff]", "", token)

            clean_chunk = []
            for char in token:
                if char == "(":
                    in_paren = True
                    paren_buffer = char
                elif in_paren:
                    paren_buffer += char
                    if char == ")":
                        tag_inner = paren_buffer[1:-1].strip().lower()
                        # If model accidentally put a voice tag in parentheses, convert to []
                        if tag_inner in VOICE_TAGS:
                            clean_chunk.append(f"[{tag_inner}]")
                        # Otherwise (e.g. gesture like (wave) or app command), discard from audio
                        paren_buffer = ""
                        in_paren = False
                elif char == "[":
                    in_bracket = True
                    bracket_buffer = char
                elif in_bracket:
                    bracket_buffer += char
                    if char == "]":
                        tag_inner = bracket_buffer[1:-1].strip().lower()
                        # If model accidentally put a gesture in square brackets (e.g. [wave]), discard from audio
                        if tag_inner in GESTURE_TAGS or tag_inner.startswith("open:") or tag_inner.startswith("close:"):
                            pass  # discard from audio
                        else:
                            clean_chunk.append(bracket_buffer)
                        bracket_buffer = ""
                        in_bracket = False
                else:
                    clean_chunk.append(char)

            filtered = "".join(clean_chunk)
            if filtered:
                accum_text += filtered
                clean_len = len(re.sub(r"\[.*?\]", "", accum_text).strip())
                has_terminal = any(p in filtered for p in terminal_punct)
                has_clause = any(p in filtered for p in clause_punct)

                if has_terminal and clean_len >= 8:
                    yield accum_text
                    accum_text = ""
                elif has_clause and clean_len >= min_chars_per_flush:
                    yield accum_text
                    accum_text = ""
                elif clean_len >= 50:
                    yield accum_text
                    accum_text = ""

        if paren_buffer and not in_paren:
            accum_text += paren_buffer
        if bracket_buffer and not in_bracket:
            accum_text += bracket_buffer

        if accum_text:
            # Only yield if remaining buffer has actual text words, omitting isolated trailing tags (e.g. [curious])
            clean_buf = re.sub(r"\[.*?\]", "", accum_text).strip()
            if clean_buf:
                yield accum_text

    tokens_iter = token_filter()
    first_token = None
    for t in tokens_iter:
        if isinstance(t, str) and t.strip():
            first_token = t
            break

    if first_token is None:
        # No text to synthesize
        audio_queue.put(None)
        return

    sent_text_chunks = [first_token]
    def recording_text_stream():
        yield first_token
        for item in tokens_iter:
            sent_text_chunks.append(item)
            yield item

    ws_failed = False
    try:
        for audio_chunk in engine.stream_realtime(recording_text_stream(), min_chunk_seconds=min_chunk_seconds):
            if collected_fragments is not None:
                collected_fragments.append(audio_chunk)
            audio_queue.put(audio_chunk)
    except Exception as e:
        ws_failed = True
        print(f"\n❌ Fish Audio realtime worker error: {e}", file=sys.stderr)

    # If WebSocket failed before producing any audio, fall back seamlessly to REST TTS
    if ws_failed and (collected_fragments is None or len(collected_fragments) == 0):
        # Drain any unread tokens remaining in tokens_iter so no text is lost
        for remaining in tokens_iter:
            sent_text_chunks.append(remaining)
        full_text = "".join(sent_text_chunks).strip()
        if full_text:
            print(f"\n🔄 Falling back to Fish Audio REST TTS...", file=sys.stderr)
            try:
                audio_data, _sr = engine.synthesize_sentence(full_text)
                if collected_fragments is not None:
                    collected_fragments.append(audio_data)
                audio_queue.put(audio_data)
            except Exception as fallback_err:
                print(f"\n❌ Fallback REST TTS also failed: {fallback_err}", file=sys.stderr)

    audio_queue.put(None)


