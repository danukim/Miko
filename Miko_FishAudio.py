import sys
import os
import time
import re
import contextlib
import threading
import traceback
from datetime import datetime

from audio_streamer import create_miko_audio_handler
from fish_audio_helpers import (
    FishAudioEngine,
    fish_audio_tts_worker,
    fish_audio_realtime_worker,
    detect_sentence_boundary,
    clean_sentence_for_tts,
)

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

_suppress_lock = threading.RLock()
_null_file = None

def _get_null_file():
    """Get or create persistent null file descriptor."""
    global _null_file
    if _null_file is None or _null_file.closed:
        _null_file = open(os.devnull, "w", encoding="utf-8", errors="ignore")
    return _null_file

def log_crash(exc=None):
    """Log unhandled exception and traceback to crash.log so it is never lost."""
    try:
        crash_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash.log")
        with open(crash_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*30} CRASH REPORT (Miko - Fish Audio): {datetime.now().isoformat()} {'='*30}\n")
            if exc is not None:
                f.write(f"Exception: {type(exc).__name__}: {exc}\n")
                traceback.print_exception(type(exc), exc, getattr(exc, "__traceback__", None), file=f)
            else:
                traceback.print_exc(file=f)
            f.write("\n")
    except Exception:
        pass

def ensure_ollama_ready(host="http://127.0.0.1:11434", timeout=8):
    """Ensure Ollama server is running. If not running, attempt to start it and wait for readiness."""
    import urllib.request
    import shutil
    import subprocess

    def _ping():
        try:
            with urllib.request.urlopen(f"{host}/api/tags", timeout=1) as resp:
                return resp.status == 200
        except Exception:
            return False

    if _ping():
        return True

    print(kawaii_gradient_text("🦙 Ollama server not detected. Starting Ollama...", "#FF69B4", "#DDA0DD"))

    ollama_bin = shutil.which("ollama")
    if not ollama_bin and os.name == "nt":
        cand = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe")
        if os.path.exists(cand):
            ollama_bin = cand

    if ollama_bin:
        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            subprocess.Popen([ollama_bin, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
        except Exception as e:
            print(f"⚠️ Could not launch Ollama: {e}")

    start_t = time.time()
    while time.time() - start_t < timeout:
        if _ping():
            print(kawaii_gradient_text("✨ Ollama server connected! ✨", "#00CED1", "#FF69B4"))
            return True
        time.sleep(0.5)

    print(kawaii_gradient_text("⚠️ Ollama is not responding on http://127.0.0.1:11434. Please run 'ollama serve' in another terminal.", "#FF69B4", "#FFA500"))
    return False

def ensure_server_ready(host="http://127.0.0.1:8000", timeout=5):
    """Ensure Unity companion server (app.py) is running on port 8000 using current venv."""
    import urllib.request
    import subprocess

    def _ping():
        try:
            with urllib.request.urlopen(f"{host}/audio_status", timeout=1) as resp:
                return resp.status == 200
        except Exception:
            return False

    if _ping():
        return True

    print(kawaii_gradient_text("🌐 Starting Unity backend server (app.py)...", "#00CED1", "#1E90FF"))
    try:
        flags = subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
        subprocess.Popen([sys.executable, "app.py"], creationflags=flags)
    except Exception as e:
        print(f"⚠️ Could not start app.py: {e}")

    start_t = time.time()
    while time.time() - start_t < timeout:
        if _ping():
            return True
        time.sleep(0.5)
    return False

@contextlib.contextmanager
def suppress_stdout_stderr():
    """Thread-safe context manager to suppress stdout and stderr output."""
    with _suppress_lock:
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        devnull = _get_null_file()
        try:
            sys.stdout = devnull
            sys.stderr = devnull
            yield
        finally:
            sys.stdout = orig_stdout if (orig_stdout and not getattr(orig_stdout, "closed", False)) else sys.__stdout__
            sys.stderr = orig_stderr if (orig_stderr and not getattr(orig_stderr, "closed", False)) else sys.__stderr__

_imports_initialized = False

def kawaii_gradient_text(text, start_color, end_color):
    """Create kawaii gradient text! (◕‿◕)"""
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    start_r, start_g, start_b = hex_to_rgb(start_color)
    end_r, end_g, end_b = hex_to_rgb(end_color)

    gradient = ""
    text_length = len(text)
    for i, char in enumerate(text):
        if text_length > 1:
            ratio = i / (text_length - 1)
        else:
            ratio = 0
        r = int(start_r + (end_r - start_r) * ratio)
        g = int(start_g + (end_g - start_g) * ratio)
        b = int(start_b + (end_b - start_b) * ratio)
        gradient += f"\033[38;2;{r};{g};{b}m{char}"
    return gradient + "\033[0m"

def kawaii_import_modules():
    """Kawaii import progress bar with colors! ✨ - Only runs once!"""
    global _imports_initialized
    if _imports_initialized:
        return

    try:
        from tqdm import tqdm
    except ImportError:
        print("Loading modules...")
        _imports_initialize_fallback()
        _imports_initialized = True
        return

    kawaii_imports = [
        ("speech_recognition", "🎤 Voice magic"),
        ("sounddevice", "🔊 Audio sparkles"),
        ("soundfile", "📁 Sound files"),
        ("torch", "🔥 AI power"),
        ("transformers", "🤖 Smart models"),
        ("tuya_connector", "🏠 Smart home"),
        ("string", "📝 Text tools"),
        ("json", "📋 Data format"),
        ("vectordb", "🧠 Memory core"),
        ("dotenv", "⚙️ Config loader"),
        ("requests", "🌐 Web requests"),
        ("datetime", "⏰ Time keeper"),
        ("asyncio", "⚡ Async magic"),
        ("ollama", "🦙 AI chat"),
        ("numpy", "🔢 Math arrays"),
        ("threading", "🧵 Multi-thread"),
        ("pynput", "⌨️ Key listener"),
        ("msvcrt", "💻 Console IO"),
        ("nltk", "📚 Text processing"),
        ("queue", "📦 Data queue"),
        ("re", "🔍 Regex patterns"),
        ("fishaudio", "🐟 Fish Audio S2.1 Pro SDK")
    ]

    print(kawaii_gradient_text("✨ Loading Miko's magical components with Fish Audio... ✨", "#FF69B4", "#00CED1"))
    print()

    with tqdm(
        total=len(kawaii_imports),
        desc=kawaii_gradient_text("🌸 Importing", "#FFB6C1", "#DDA0DD"),
        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] {postfix}',
        colour='magenta',
        ascii=False,
        ncols=80
    ) as pbar:
        for module_name, description in kawaii_imports:
            pbar.set_postfix_str(kawaii_gradient_text(description, "#FF1493", "#00BFFF"))
            try:
                if module_name == "speech_recognition":
                    with suppress_stdout_stderr():
                        import speech_recognition as sr
                    globals()['sr'] = sr
                elif module_name == "sounddevice":
                    with suppress_stdout_stderr():
                        import sounddevice as sd
                    globals()['sd'] = sd
                elif module_name == "soundfile":
                    with suppress_stdout_stderr():
                        import soundfile as sf
                    globals()['sf'] = sf
                elif module_name == "torch":
                    with suppress_stdout_stderr():
                        import torch
                    globals()['torch'] = torch
                elif module_name == "transformers":
                    with suppress_stdout_stderr():
                        from transformers import AutoTokenizer, AutoModelForSequenceClassification
                    globals()['AutoTokenizer'] = AutoTokenizer
                    globals()['AutoModelForSequenceClassification'] = AutoModelForSequenceClassification
                elif module_name == "tuya_connector":
                    with suppress_stdout_stderr():
                        from tuya_connector import TuyaOpenAPI
                    globals()['TuyaOpenAPI'] = TuyaOpenAPI
                elif module_name == "string":
                    import string
                    globals()['string'] = string
                elif module_name == "json":
                    import json
                    globals()['json'] = json
                elif module_name == "vectordb":
                    with suppress_stdout_stderr():
                        from vectordb import Memory
                        from memory_enhanced import EnhancedMemory
                    globals()['Memory'] = Memory
                    globals()['EnhancedMemory'] = EnhancedMemory
                elif module_name == "dotenv":
                    with suppress_stdout_stderr():
                        from dotenv import load_dotenv
                    globals()['load_dotenv'] = load_dotenv
                elif module_name == "requests":
                    import requests
                    globals()['requests'] = requests
                elif module_name == "datetime":
                    from datetime import datetime
                    globals()['datetime'] = datetime
                elif module_name == "asyncio":
                    import asyncio
                    globals()['asyncio'] = asyncio
                elif module_name == "ollama":
                    with suppress_stdout_stderr():
                        import ollama
                    globals()['ollama'] = ollama
                elif module_name == "numpy":
                    import numpy as np
                    globals()['np'] = np
                elif module_name == "threading":
                    import threading
                    globals()['threading'] = threading
                elif module_name == "pynput":
                    with suppress_stdout_stderr():
                        from pynput import keyboard
                    globals()['keyboard'] = keyboard
                elif module_name == "msvcrt":
                    import msvcrt
                    globals()['msvcrt'] = msvcrt
                elif module_name == "nltk":
                    with suppress_stdout_stderr():
                        import nltk
                    globals()['nltk'] = nltk
                elif module_name == "queue":
                    import queue
                    globals()['queue'] = queue
                elif module_name == "re":
                    import re
                    globals()['re'] = re
                elif module_name == "fishaudio":
                    with suppress_stdout_stderr():
                        import fishaudio
                    globals()['fishaudio'] = fishaudio

                time.sleep(0.04)
            except ImportError:
                pbar.set_postfix_str(kawaii_gradient_text(f"❌ Failed: {description}", "#FF0000", "#8B0000"))
                time.sleep(0.1)

            pbar.update(1)

    print()
    print(kawaii_gradient_text("🎀 All components loaded successfully! Ready to chat~ 🎀", "#FF1493", "#00CED1"))
    print()
    _imports_initialized = True

def _imports_initialize_fallback():
    """Fallback import without fancy progress bar."""
    with suppress_stdout_stderr():
        import speech_recognition as sr
        import sounddevice as sd
        import soundfile as sf
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        from tuya_connector import TuyaOpenAPI
        import string
        import json
        from vectordb import Memory
        from memory_enhanced import EnhancedMemory
        from dotenv import load_dotenv
        import requests
        from datetime import datetime
        import asyncio
        import ollama
        import numpy as np
        import threading
        from pynput import keyboard
        import msvcrt
        import nltk
        import queue
        import re
        import fishaudio

    globals().update({
        'sr': sr, 'sd': sd, 'sf': sf, 'torch': torch,
        'AutoTokenizer': AutoTokenizer, 'AutoModelForSequenceClassification': AutoModelForSequenceClassification,
        'TuyaOpenAPI': TuyaOpenAPI, 'string': string, 'json': json, 'Memory': Memory,
        'EnhancedMemory': EnhancedMemory, 'load_dotenv': load_dotenv, 'requests': requests, 'datetime': datetime,
        'asyncio': asyncio, 'ollama': ollama, 'np': np, 'threading': threading,
        'keyboard': keyboard, 'msvcrt': msvcrt, 'nltk': nltk, 'queue': queue, 're': re,
        'fishaudio': fishaudio
    })

def supports_color():
    """Check if terminal supports ANSI colors."""
    if os.name == 'nt':
        try:
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            if handle == -1:
                return False
            mode = wintypes.DWORD()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                return False
            new_mode = mode.value | 0x0004
            success = kernel32.SetConsoleMode(handle, new_mode)
            return bool(success)
        except Exception:
            return False
    return True

def gradient_text(text, start_color, end_color):
    """Create gradient colored text for terminal output."""
    if not supports_color():
        return f"[{text}]"

    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    start_r, start_g, start_b = hex_to_rgb(start_color)
    end_r, end_g, end_b = hex_to_rgb(end_color)

    gradient = ""
    text_length = len(text)
    for i, char in enumerate(text):
        ratio = i / (text_length - 1) if text_length > 1 else 0
        r = int(start_r + (end_r - start_r) * ratio)
        g = int(start_g + (end_g - start_g) * ratio)
        b = int(start_b + (end_b - start_b) * ratio)
        gradient += f"\033[38;2;{r};{g};{b}m{char}"
    return gradient + "\033[0m"

def typewriter_effect(text, delay=0.03):
    """Display text with typewriter effect while preserving ANSI color gradients."""
    lines = text.split('\n')
    for line in lines:
        i = 0
        while i < len(line):
            char = line[i]
            if char == '\033':
                escape_start = i
                i += 1
                while i < len(line) and line[i] != 'm':
                    i += 1
                if i < len(line):
                    i += 1
                escape_seq = line[escape_start:i]
                print(escape_seq, end="", flush=True)
                if i < len(line):
                    print(line[i], end="", flush=True)
                    time.sleep(delay)
                    i += 1
            else:
                print(char, end="", flush=True)
                time.sleep(delay)
                i += 1
        print()

def strip_ansi_codes(text):
    """Remove ANSI color codes for length calculation."""
    ansi_escape = re.compile(r"\033\[[0-9;]*[mK]")
    return ansi_escape.sub("", text)

def initialize_and_run():
    """Initialize and run the Miko AI companion powered by Fish Audio S2.1 Pro."""
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    kawaii_import_modules()

    # Disable future tqdm progress bars
    try:
        import tqdm
        if hasattr(tqdm, 'tqdm'):
            original_tqdm_init = tqdm.tqdm.__init__
            def new_tqdm_init(self, *args, **kwargs):
                kwargs['disable'] = True
                original_tqdm_init(self, *args, **kwargs)
            tqdm.tqdm.__init__ = new_tqdm_init
    except (ImportError, AttributeError):
        pass

    global sr, sd, sf, torch, AutoTokenizer, AutoModelForSequenceClassification, TuyaOpenAPI
    global string, json, Memory, EnhancedMemory, load_dotenv, requests, datetime, asyncio, ollama, np
    global threading, keyboard, msvcrt, nltk, queue, re, fishaudio

    supports_color()

    with suppress_stdout_stderr():
        nltk.download("punkt_tab", quiet=True)

    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    load_dotenv()

    # Ensure Ollama server is running
    ensure_ollama_ready()

    # Preload Ollama model asynchronously
    def warmup_ollama_background():
        try:
            llm_model = os.getenv("LLM_MODEL")
            if llm_model:
                ollama.generate(model=llm_model, prompt="", keep_alive=-1)
        except Exception:
            pass

    threading.Thread(target=warmup_ollama_background, daemon=True).start()

    # Initialize shared audio handler for animations
    global animation_handler
    animation_handler = None

    def audio_playback_thread(audio_queue: queue.Queue, sample_rate: int):
        """Streams normalized float32 audio chunks to Unity while keeping local timing."""
        global animation_handler
        server_ip = os.getenv("IP_ADDRESS", "127.0.0.1")
        if server_ip == "localhost":
            server_ip = "127.0.0.1"
        local_vol = float(os.getenv("LOCAL_AUDIO_VOLUME", "0.0"))
        dual_player = create_miko_audio_handler(
            server_url=f"http://{server_ip}:8000",
            local_volume=local_vol
        )
        animation_handler = dual_player
        started = False

        try:
            while True:
                try:
                    audio_fragment = audio_queue.get(timeout=1.0)
                    if audio_fragment is None:
                        break

                    if audio_fragment.dtype != np.float32:
                        audio_fragment = audio_fragment.astype(np.float32)

                    if not started:
                        dual_player.start_playback(sample_rate)
                        started = True

                    # Fish Audio samples are normalized float32 in [-1.0, 1.0]
                    normalized_fragment = np.clip(audio_fragment, -1.0, 1.0)
                    dual_player.add_audio_chunk(normalized_fragment)

                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"❌ Audio playback error: {e}")
                    break
        finally:
            if started:
                dual_player.stop_playback()

    # Ensure Unity companion server is running
    ensure_server_ready()

    # Display startup banner
    START_COLOR = "#00FFFF"  # Aqua/Cyan
    END_COLOR = "#FFD700"    # Gold

    ascii_art = """
     ____             ______           _ _ _
    / __ \\           |  __  \\         | (_) |
   | |  | |_ __   ___| |__) |___  __ _| |_| |_ _   _
   | |  | | '_ \\ / _ \\  _  // _ \\/ _` | | | __| | | |
   | |__| | | | |  __/ | \\ \\  __/ (_| | | | |_| |_| |
    \\____/|_| |_|\\___|_|  \\_\\___|\\__,_|_|_|\\__|\\__, |
                                               __/ /
                                              |___/
    """
    print(ascii_art)
    text = (
        "Redefining Reality\n"
        "[PROJECT M.I.T.S.U.H.A. - Fish Audio S2.1 Pro Free Edition]\n"
        + gradient_text("DogeLord", START_COLOR, END_COLOR)
    )

    ascii_art_width = max(len(line) for line in ascii_art.splitlines())
    centered_lines = []
    for line in text.splitlines():
        stripped_line = strip_ansi_codes(line)
        padding = (ascii_art_width - len(stripped_line)) // 2
        centered_line = " " * padding + line
        centered_lines.append(centered_line)

    typewriter_effect("\n".join(centered_lines))
    print("\n")

    # Configure input mode
    input_mode = input("Select input mode: [V] Voice [T] Typing: ").lower()
    if input_mode == "t":
        use_typing_mode = True
        push_to_talk = False
    else:
        use_typing_mode = False
        if input_mode == "v":
            mode_choice = input("Push to talk or always listening? [P] Push to talk [A] Always listening: ")
            push_to_talk = mode_choice.lower() == "p"
        else:
            push_to_talk = False

    tuya = os.getenv("USE_TUYA")
    lang_code = os.getenv("LANGUAGE", "auto").strip().lower()

    # Initialize enhanced conversation memory
    print(kawaii_gradient_text("🧠 Loading memories... ", "#FFB6C1", "#DDA0DD"), end="", flush=True)
    with suppress_stdout_stderr():
        base_memory = Memory()
        if not os.path.exists("conversation.jsonl"):
            open("conversation.jsonl", "w", encoding="utf-8").close()
        with open("conversation.jsonl", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            conversation_data = [json.dumps(json.loads(line)) for line in lines]
        if conversation_data:
            base_memory.save(conversation_data)
        memory = EnhancedMemory(base_memory, "conversation.jsonl")
    print(kawaii_gradient_text("✨ Done! ✨", "#90EE90", "#32CD32"))

    # Initialize speech-to-text recorder (voice mode only)
    recorder = None
    if not use_typing_mode:
        def on_recording_start():
            pass

        def on_recording_stop():
            pass

        def on_realtime_transcription_update(text):
            pass

        def preprocess_text(text):
            hallucinations = [
                "Conversation ends.",
                "Subtitle by",
                "Amara.org",
                "Thanks for watching",
                "MBC",
                "SBS"
            ]
            for h in hallucinations:
                if h.lower() in text.lower():
                    return ""

            text = text.lstrip()
            if text.startswith("..."):
                text = text[3:]
            text = text.strip("'\"").lstrip()
            if text:
                text = text[0].upper() + text[1:]
            return text

        if lang_code in ["auto", "", "none"]:
            stt_language = ""
            initial_prompt = (
                "You are speaking with Miko (ミコ), an AI companion. "
                "Conversations can be in English, Japanese (日本語), or other languages. "
                "Add periods only for complete sentences. "
                "Examples: 'Hello Miko, how are you today?', 'こんにちは、ミコちゃん！今日はいい天気ですね。'"
            )
        else:
            stt_language = lang_code
            initial_prompt = (
                "You are speaking with Miko, an AI assistant. "
                "Add periods only for complete sentences. "
                "Use ellipsis (...) for unfinished thoughts or unclear endings. "
                "Examples:\n"
                "'Hello Miko, how are you today?'\n"
                "'I was wondering if you could help me with...'\n"
                "'Miko, can you tell me about...'"
            )

        unknown_sentence_detection_pause = 0.7
        print(kawaii_gradient_text("🎤 Setting up voice recognition magic... ", "#FF69B4", "#DDA0DD"), end="", flush=True)
        with suppress_stdout_stderr():
            from RealtimeSTT import AudioToTextRecorder
            recorder = AudioToTextRecorder(
                on_recording_start=on_recording_start,
                on_recording_stop=on_recording_stop,
                on_realtime_transcription_update=on_realtime_transcription_update,
                spinner=False,
                use_microphone=True,
                model=os.getenv("REALTIMESTT_MODEL", "large-v2"),
                realtime_model_type=os.getenv("REALTIMESTT_MODEL", "large-v2"),
                language=stt_language,
                silero_sensitivity=0.05,
                webrtc_sensitivity=3,
                post_speech_silence_duration=unknown_sentence_detection_pause,
                min_length_of_recording=1.1,
                min_gap_between_recordings=0,
                enable_realtime_transcription=False,
                realtime_processing_pause=0.02,
                silero_deactivity_detection=True,
                early_transcription_on_silence=0.2,
                beam_size=5,
                beam_size_realtime=3,
                initial_prompt=initial_prompt,
            )
        print(kawaii_gradient_text("Voice recognition ready!", "#90EE90", "#32CD32"))
    else:
        print(kawaii_gradient_text("📝 Typing mode selected - Voice recognition skipped! ✨", "#FFB6C1", "#DDA0DD"))

    # Initialize Fish Audio engine
    print(kawaii_gradient_text("🐟 Initializing Fish Audio... ", "#00CED1", "#1E90FF"), end="", flush=True)
    fish_api_key = os.getenv("FISH_API_KEY")
    fish_model = os.getenv("FISH_AUDIO_MODEL", "s2.1-pro-free")
    target_sample_rate = int(os.getenv("FISH_AUDIO_SAMPLE_RATE", "44100"))
    ref_audio_file = os.getenv("FISH_AUDIO_REF_AUDIO") or os.getenv("GPT_SOVITS_REF_AUDIO", "Kokomi_0.wav")
    ref_prompt_text = os.getenv("FISH_AUDIO_PROMPT_TEXT") or os.getenv("GPT_SOVITS_PROMPT_TEXT")

    fish_engine = FishAudioEngine(
        api_key=fish_api_key,
        model=fish_model,
        reference_id=os.getenv("FISH_AUDIO_REFERENCE_ID"),
        ref_audio_path=ref_audio_file,
        ref_prompt_text=ref_prompt_text,
        target_sample_rate=target_sample_rate,
        chunk_size=2048,
    )

    if not fish_engine.is_configured():
        print()
        print(kawaii_gradient_text("⚠️ FISH_API_KEY not found in .env or environment!", "#FFA500", "#FF4500"))
        print(kawaii_gradient_text("👉 Get your API key at https://fish.audio/app/api-keys and set FISH_API_KEY in .env", "#FFB6C1", "#DDA0DD"))
        print(kawaii_gradient_text("   Voice audio will be disabled until FISH_API_KEY is configured.", "#FFB6C1", "#DDA0DD"))
    else:
        voice_desc = f"Voice Model: {fish_engine.reference_id}" if fish_engine.reference_id else "Zero-shot cloning (Kokomi_0.wav)"
        print(kawaii_gradient_text(f"✨ Engine ready! [{voice_desc} | Rate: {target_sample_rate}Hz] ✨", "#90EE90", "#32CD32"))

    # Configure Tuya smart home integration
    if tuya:
        ACCESS_ID = os.getenv("TUYA_ID")
        ACCESS_KEY = os.getenv("TUYA_SECRET")
        API_ENDPOINT = os.getenv("TUYA_ENDPOINT")

    # Initialize NLI model for device control
    print(kawaii_gradient_text("🤖 Loading transformers... ", "#00CED1", "#1E90FF"), end="", flush=True)
    with suppress_stdout_stderr():
        transformer_model = os.getenv("NLI_RTE_TRANSFORMER", "typeform/distilbert-base-uncased-mnli")
        tokenizer = AutoTokenizer.from_pretrained(transformer_model)
        model = AutoModelForSequenceClassification.from_pretrained(transformer_model)
    print(kawaii_gradient_text("✨ Transformers ready! ✨", "#90EE90", "#32CD32"))

    # Load system prompt for AI personality
    lore = os.getenv("LORE")
    lore = {"role": "system", "content": f"{lore}"}
    lore = json.dumps(lore)

    def clear_input_buffer():
        while msvcrt.kbhit():
            msvcrt.getch()

    p_key_pressed = False

    def on_press(key):
        nonlocal p_key_pressed
        try:
            if key.char == "p":
                p_key_pressed = True
        except AttributeError:
            pass

    def on_release(key):
        nonlocal p_key_pressed
        try:
            if key.char == "p":
                p_key_pressed = False
        except AttributeError:
            pass

    def check_goodbye(transcript):
        goodbye_words = ["bye", "goodbye", "see you"]
        tokens = nltk.word_tokenize(transcript.lower())
        return any(word in tokens for word in goodbye_words)

    def test_entailment(text1, text2):
        batch = tokenizer(text1, text2, return_tensors="pt").to(model.device)
        with suppress_stdout_stderr():
            with torch.no_grad():
                proba = torch.softmax(model(**batch).logits, -1)
        return proba.cpu().numpy()[0, model.config.label2id["ENTAILMENT"]]

    def test_equivalence(text1, text2):
        return test_entailment(text1, text2) * test_entailment(text2, text1)

    def replace_device(sentence, word):
        return sentence.replace("[device]", word)

    def keep_sentence_with_word(text, word):
        sentences = re.split(r"[.,!?]", text)
        filtered_sentences = [
            sentence.strip() + punct
            for sentence, punct in zip(sentences, re.findall(r"[.,!?]", text))
            if word in sentence
        ]
        return " ".join(filtered_sentences)

    run_count = 0

    if not use_typing_mode:
        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()

    async def heart():
        """Main conversation loop."""
        nonlocal run_count

        while True:
            try:
                if use_typing_mode:
                    print(kawaii_gradient_text("\nType your message to Miko~ (or 'quit' to exit):", "#FFB6C1", "#DDA0DD"))
                    print(kawaii_gradient_text("You: ", "#00CED1", "#1E90FF"), end="", flush=True)
                    text = input().strip()

                    if text.lower() in ["quit", "exit", "bye", "goodbye"]:
                        break
                    if not text:
                        continue
                    trans = text
                else:
                    trans = ""

                    def process_complete_text(spoken_text):
                        nonlocal trans
                        spoken_text = preprocess_text(spoken_text)
                        trans = spoken_text
                        print(f"\r{' ' * 50}\r", end="", flush=True)
                        print(kawaii_gradient_text("You: ", "#00CED1", "#1E90FF") + spoken_text)

                    if push_to_talk:
                        print(kawaii_gradient_text("\nPress 'p' to speak with Miko~", "#FF69B4", "#FF1493"))
                        while not p_key_pressed:
                            await asyncio.sleep(0.1)
                        print(kawaii_gradient_text("Listening... ", "#FFD700", "#FFA500"), end="", flush=True)
                        recorder.text(process_complete_text)
                    else:
                        print(kawaii_gradient_text("🎧 Always listening for you~ ", "#DDA0DD", "#9370DB"), end="", flush=True)
                        recorder.text(process_complete_text)

                    if not trans or len(trans.strip()) == 0:
                        print(kawaii_gradient_text("😔 No speech detected... Trying again~ ", "#FFA07A", "#FA8072"))
                        continue

                now = datetime.now()
                date = now.strftime("%m/%d/%Y")
                time_2 = now.strftime("%H:%M:%S")

            except Exception:
                continue

            text = trans
            if text.startswith("Miko- "):
                text = text[6:]
            elif text.startswith("Mitsuha- "):
                text = text[9:]

            new_line = {
                "role": "user",
                "date": date,
                "time": time_2,
                "content": text,
            }

            clear_input_buffer()

            with suppress_stdout_stderr():
                memory.save_with_metadata(new_line)

            # Smart home device control
            devices = [os.getenv("DEVICE_1"), os.getenv("DEVICE_2")]
            if tuya:
                sentence = "Activate [device]."
                input_sentence = trans.lower()
                for word in devices:
                    if word and word in input_sentence:
                        try:
                            modified_sentence = replace_device(sentence, word)
                            input_sentence = keep_sentence_with_word(input_sentence, word)
                            input_sentence = input_sentence.translate(str.maketrans("", "", string.punctuation))
                            similarity = test_equivalence(modified_sentence, input_sentence)

                            openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_KEY)
                            openapi.connect()

                            if similarity >= 0.5:
                                commands = {"commands": [{"code": "switch_1", "value": True}]}
                            elif similarity < 0.001:
                                commands = {"commands": [{"code": "switch_1", "value": False}]}
                            else:
                                continue

                            if word == os.getenv("DEVICE_1"):
                                openapi.post(os.getenv("DEVICE_1_ID"), commands)
                            elif word == os.getenv("DEVICE_2"):
                                openapi.post(os.getenv("DEVICE_2_ID"), commands)
                        except (requests.exceptions.JSONDecodeError, Exception) as e:
                            print(f"Tuya API error: {e}")
                            pass

            # Retrieve relevant conversation history
            query = f"{text}"
            current_time = datetime.now()

            with suppress_stdout_stderr():
                repetition_info = memory.detect_repetition(query, current_time, time_window_hours=24)
                smart_results = memory.search_smart(query, current_time, top_n=5)

            if len(smart_results) >= 2:
                line1 = smart_results[0]['chunk']
                line2 = smart_results[1]['chunk']
                line1_dict = json.dumps(json.loads(line1), separators=(",", ":"))
                line2_dict = json.dumps(json.loads(line2), separators=(",", ":"))
            else:
                line1 = json.dumps({"role": "system", "content": "No relevant memories"})
                line2 = line1
                line1_dict = line1
                line2_dict = line2

            with open("conversation.jsonl", "r", encoding="UTF-8") as file:
                lines = [line.strip() for line in file.readlines() if line.strip()]

            if len(lines) >= 6:
                if run_count >= 3:
                    last_six_lines = "\n".join(lines[-6:])
                elif run_count == 0:
                    last_six_lines = line1 + "\n" + line2
                else:
                    last_six_lines = "\n".join(lines[-2 * run_count :])

                if last_six_lines:
                    for i, line in enumerate(lines):
                        if line == line1_dict:
                            if '''{"role":"user"''' in line:
                                last_six_lines = line1 + "\n" + str(lines[i + 1]) + "\n" + last_six_lines
                            elif '''{"role":"assistant"''' in line:
                                last_six_lines = str(lines[i - 1]) + "\n" + line1 + "\n" + last_six_lines
                            break
                    for i, line in enumerate(lines):
                        if line == line2_dict:
                            if '''{"role":"user"''' in line:
                                last_six_lines = line2 + "\n" + str(lines[i + 1]) + "\n" + last_six_lines
                            elif '''{"role":"assistant"''' in line:
                                last_six_lines = str(lines[i - 1]) + "\n" + line2 + "\n" + last_six_lines
                            break
            else:
                last_six_lines = "\n".join(lines) if lines else ""

            last_six_lines = [json.loads(line) for line in last_six_lines.split("\n") if line.strip()]

            cleaned_lines = []
            for line in last_six_lines:
                if "content" in line:
                    content = line["content"]
                    content = re.sub(r'^\d{4}-\d{2}-\d{2} / \d{2}:\d{2}:\d{2} / ', '', content)
                    content = re.sub(r'^\d{2}/\d{2}/\d{4} / \d{2}:\d{2}:\d{2} / ', '', content)
                    # Normalize historical bracketed gestures [wave] -> (wave) so LLM learns proper formatting
                    content = re.sub(r'\[(wave|thumbs-up|thumbs- up|nodding|shaking head|shaking- head|clap)\]', r'(\1)', content, flags=re.IGNORECASE)
                    # Normalize historical parenthesized voice tags (whisper) -> [whisper]
                    content = re.sub(r'\((excited|whisper|cheerful|curious|pouty|tender|teasing|sarcastic|giggle|chuckle|sigh|gasp|yawn|playful)\)', r'[\1]', content, flags=re.IGNORECASE)
                    line["content"] = content
                cleaned_lines.append(line)

            now = datetime.now()
            date = now.strftime("%m/%d/%Y")
            time_1 = now.strftime("%H:%M:%S")

            lore_dict = json.loads(lore)
            new_line_dict = json.loads(json.dumps(new_line))

            if "content" in new_line_dict:
                content = new_line_dict["content"]
                content = re.sub(r'^\d{4}-\d{2}-\d{2} / \d{2}:\d{2}:\d{2} / ', '', content)
                content = re.sub(r'^\d{2}/\d{2}/\d{4} / \d{2}:\d{2}:\d{2} / ', '', content)
                new_line_dict["content"] = content

            temporal_context = f"\nCurrent date/time: {date} {time_1}."
            if repetition_info:
                hours = repetition_info['hours_ago']
                if hours < 1:
                    time_ref = f"{int(hours * 60)} minutes ago"
                elif hours < 24:
                    time_ref = f"{int(hours)} hours ago"
                else:
                    time_ref = f"{int(hours / 24)} days ago"
                temporal_context += f" Note: User asked a similar question ({repetition_info['previous_query']}) {time_ref}. You may acknowledge this naturally if appropriate."

            lore_dict['content'] += temporal_context

            if fish_engine.is_configured():
                lore_dict['content'] += (
                    "\n\nFormatting & Output Mandates:\n"
                    "1. PHYSICAL AVATAR ANIMATIONS (Unity Body Motions):\n"
                    "   - You MUST place exactly ONE body gesture at the VERY END of your entire response as the final token, enclosed in PARENTHESES: (wave), (thumbs-up), (nodding), (shaking head), or (clap).\n"
                    "   - Use (wave) for all greetings.\n"
                    "   - CRITICAL RULE: Body animations MUST ALWAYS be in PARENTHESES `(...)`. NEVER put body animations in square brackets like `[wave]`!\n"
                    "   - CRITICAL RULE: NEVER place body animations mid-sentence. Place it only at the very end.\n"
                    "   - CRITICAL RULE: NEVER invent fake gestures in parentheses like (playful), (smiles), or (giggles). Only the 5 allowed gestures above may use parentheses.\n\n"
                    "2. FISH AUDIO EXPRESSIVE VOCAL TAGS:\n"
                    "   - Your voice engine supports natural expression tags enclosed in SQUARE BRACKETS `[...]`.\n"
                    "   - Valid tags you may use naturally (1-2 per response):\n"
                    "     * Emotions: [excited], [whisper], [cheerful], [curious], [pouty], [tender], [teasing], [sarcastic]\n"
                    "     * Nuances: [giggle], [chuckle], [sigh], [gasp], [yawn]\n"
                    "     * Pauses: [short pause], [long pause]\n"
                    "   - CRITICAL RULE: Voice tags MUST ALWAYS be in SQUARE BRACKETS `[...]`. NEVER put emotion/vocal tags in parentheses like `(playful)` or `(whisper)`!\n"
                    "   - CRITICAL RULE: Do NOT output emojis.\n"
                    "   - Example response:\n"
                    "     '[excited] Oh, hey there! Just chilling after a long day at school. [giggle] What about you? (wave)'\n\n"
                    "3. DYNAMIC MULTILINGUAL CODE-SWITCHING MANDATE:\n"
                    "   - You are fully bilingual and fluent in English and Japanese (日本語).\n"
                    "   - CRITICAL LANGUAGE RULE: Automatically detect whatever language the user speaks in each message.\n"
                    "     * If the user speaks Japanese, you MUST respond completely and naturally in Japanese using proper native script (Kanji, Hiragana, Katakana). NEVER respond in English to Japanese speech.\n"
                    "     * If the user speaks English, you MUST respond completely in English.\n"
                    "     * If the user switches languages between turns, you MUST switch your response language instantly to match.\n"
                    "   - Keep your responses concise (1-2 sentences) in the matched language.\n"
                    "   - In Japanese responses, you may still use the voice tags e.g. [cheerful] and physical gesture at the end e.g. (wave).\n"
                )

            prompt = [lore_dict, *cleaned_lines, new_line_dict]

            emotion_hotkey_map = {
                "(wave)": "6", "[wave]": "6",
                "(thumbs-up)": "7", "[thumbs-up]": "7",
                "(thumbs- up)": "7", "[thumbs- up]": "7",
                "(nodding)": "8", "[nodding]": "8",
                "(shaking head)": "9", "[shaking head]": "9",
                "(shaking- head)": "9", "[shaking- head]": "9",
                "(clap)": "10", "[clap]": "10"
            }

            emotion_to_animation = {
                "(wave)": "Wave", "[wave]": "Wave",
                "(thumbs-up)": "Thumbs-up", "[thumbs-up]": "Thumbs-up",
                "(thumbs- up)": "Thumbs-up", "[thumbs- up]": "Thumbs-up",
                "(nodding)": "Nodding", "[nodding]": "Nodding",
                "(shaking head)": "Shaking head", "[shaking head]": "Shaking head",
                "(shaking- head)": "Shaking head", "[shaking- head]": "Shaking head",
                "(clap)": "Clap", "[clap]": "Clap"
            }

            print(kawaii_gradient_text("Miko: ", "#FF69B4", "#DDA0DD"), end="")
            response = ""
            display_buffer = ""

            use_realtime_streaming = os.getenv("FISH_AUDIO_STREAMING", "true").lower() in ["true", "1", "yes"]

            # Initialize concurrent Fish Audio TTS
            token_queue = queue.Queue()
            tts_queue = queue.Queue()
            audio_queue = queue.Queue()
            collected_fragments = []

            playback_thread = threading.Thread(
                target=audio_playback_thread, args=(audio_queue, target_sample_rate)
            )
            playback_thread.start()

            if fish_engine.is_configured():
                if use_realtime_streaming:
                    min_chars = int(os.getenv("FISH_AUDIO_MIN_CHARS", "20"))
                    min_chunk = float(os.getenv("FISH_AUDIO_MIN_CHUNK", "0.0"))
                    tts_worker_thread = threading.Thread(
                        target=fish_audio_realtime_worker,
                        args=(token_queue, audio_queue, fish_engine, collected_fragments, min_chars, min_chunk),
                        daemon=True
                    )
                else:
                    tts_worker_thread = threading.Thread(
                        target=fish_audio_tts_worker,
                        args=(tts_queue, audio_queue, fish_engine, collected_fragments),
                        daemon=True
                    )
                tts_worker_thread.start()
            else:
                tts_worker_thread = None

            sentence_buffer = ""

            try:
                for chunk in ollama.chat(model=os.getenv("LLM_MODEL"), messages=prompt, stream=True, keep_alive=-1):
                    chunk_content = chunk["message"]["content"]
                    response += chunk_content
                    display_buffer += chunk_content

                    if use_realtime_streaming:
                        if fish_engine.is_configured():
                            token_queue.put(chunk_content)
                    else:
                        sentence_buffer += chunk_content
                        if detect_sentence_boundary(sentence_buffer):
                            clean_sent = clean_sentence_for_tts(sentence_buffer)
                            if clean_sent and fish_engine.is_configured():
                                tts_queue.put(clean_sent)
                            sentence_buffer = ""

                    while True:
                        emotion_found = False
                        for emotion in emotion_hotkey_map:
                            if emotion in display_buffer:
                                parts = display_buffer.split(emotion, 1)
                                if parts[0]:
                                    print(parts[0], end="", flush=True)

                                if emotion in emotion_to_animation:
                                    animation_name = emotion_to_animation[emotion]
                                    if animation_handler:
                                        try:
                                            animation_handler.send_animation(animation_name)
                                        except Exception:
                                            pass

                                display_buffer = parts[1] if len(parts) > 1 else ""
                                emotion_found = True
                                break

                        if not emotion_found:
                            safe_to_display = True
                            for emotion in emotion_hotkey_map:
                                for i in range(1, len(emotion)):
                                    if display_buffer.endswith(emotion[:i]):
                                        safe_to_display = False
                                        break
                                if not safe_to_display:
                                    break

                            if safe_to_display and display_buffer:
                                print(display_buffer, end="", flush=True)
                                display_buffer = ""
                            break

            except Exception as e:
                print(kawaii_gradient_text(f"\n❌ Ollama chat error: {e}", "#FF69B4", "#FFA500"))
                print(kawaii_gradient_text("⚠️ Ensure Ollama is running (`ollama serve`). Waiting for next message...", "#FFB6C1", "#DDA0DD"))
                if use_realtime_streaming:
                    token_queue.put(None)
                else:
                    tts_queue.put(None)
                audio_queue.put(None)
                try:
                    playback_thread.join(timeout=1.0)
                    if tts_worker_thread:
                        tts_worker_thread.join(timeout=1.0)
                except Exception:
                    pass
                continue

            if display_buffer:
                display_buffer = re.sub(r'[\(\[][^)\]]*(?:wave|thumbs|nod|shak|clap)[\)\]]', '', display_buffer, flags=re.IGNORECASE)
                for emotion in emotion_hotkey_map:
                    display_buffer = display_buffer.replace(emotion, "")
                if display_buffer.strip():
                    print(display_buffer, end="", flush=True)

            print()

            # Normalize response before storing so future in-context memory has valid (gesture) format
            normalized_response = re.sub(
                r'\[(wave|thumbs-up|thumbs- up|nodding|shaking head|shaking- head|clap)\]',
                r'(\1)',
                response,
                flags=re.IGNORECASE
            )
            new_line = {"role": "assistant", "date": date, "time": time_1, "content": normalized_response}
            with suppress_stdout_stderr():
                memory.save_with_metadata(new_line)

            if use_realtime_streaming:
                token_queue.put(None)
            else:
                if sentence_buffer and fish_engine.is_configured():
                    clean_sent = clean_sentence_for_tts(sentence_buffer)
                    if clean_sent:
                        tts_queue.put(clean_sent)
                tts_queue.put(None)

            # Signal TTS worker to stop and wait
            if tts_worker_thread:
                tts_worker_thread.join()

            # Signal playback to stop and wait
            audio_queue.put(None)
            playback_thread.join()

            # Determine filename based on emotions
            filename = "out.wav"
            for emotion in emotion_hotkey_map:
                if emotion in response:
                    emotion_name = emotion.strip("()[]")
                    filename = f"{emotion_name}.wav"
                    break

            if collected_fragments:
                try:
                    full_audio = np.concatenate(collected_fragments)
                    # Samples are normalized float32 in [-1.0, 1.0]
                    sf.write(filename, full_audio, target_sample_rate)
                except Exception:
                    pass

            run_count += 1

            if use_typing_mode:
                continue
            elif check_goodbye(trans):
                break

    try:
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        asyncio.run(heart())
    except KeyboardInterrupt:
        print(kawaii_gradient_text("\n🌸 Miko is going to sleep now... Goodbye! 🌸", "#FF69B4", "#DDA0DD"))
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        traceback.print_exc()
        log_crash(e)
        print(kawaii_gradient_text("\n📝 Crash details logged to crash.log", "#FF69B4", "#DDA0DD"))
        try:
            input("\nPress Enter to exit...")
        except Exception:
            pass
    finally:
        print(kawaii_gradient_text("✨ Shutting down gracefully... ✨", "#FFB6C1", "#DDA0DD"))
        if not use_typing_mode and recorder is not None:
            try:
                recorder.shutdown()
            except Exception:
                pass

        if not use_typing_mode and 'listener' in locals():
            try:
                listener.stop()
            except Exception:
                pass

        print(kawaii_gradient_text("💫 Application terminated. See you next time! 💫", "#FF1493", "#00CED1"))


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    try:
        initialize_and_run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"\n❌ Fatal startup error: {e}")
        traceback.print_exc()
        log_crash(e)
        print("\n📝 Crash details logged to crash.log")
        try:
            input("\nPress Enter to exit...")
        except Exception:
            pass
