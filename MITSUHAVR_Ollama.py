import contextlib
from audio_streamer import create_mitsuha_audio_handler

@contextlib.contextmanager
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

# Basic imports needed for the kawaii loader
import sys
import os
import time

# Flag to track if imports have been done
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
        return  # Already imported, skip the kawaii show
    
    try:
        from tqdm import tqdm
    except ImportError:
        # Fallback if tqdm not available
        print("Loading modules...")
        _imports_initialize_fallback()
        _imports_initialized = True
        return

    # Kawaii import list with descriptions ♡
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
        ("re", "🔍 Regex patterns")
    ]

    print(kawaii_gradient_text("✨ Loading Mitsuha's magical components... ✨", "#FF69B4", "#00CED1"))
    print()

    # Create kawaii progress bar
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
                
                time.sleep(0.05)  # Kawaii delay for visual effect ♡
                
            except ImportError as e:
                pbar.set_postfix_str(kawaii_gradient_text(f"❌ Failed: {description}", "#FF0000", "#8B0000"))
                time.sleep(0.1)
            
            pbar.update(1)

    print()
    print(kawaii_gradient_text("🎀 All components loaded successfully! Ready to chat~ 🎀", "#FF1493", "#00CED1"))
    print()
    
    _imports_initialized = True

def _imports_initialize_fallback():
    """Fallback import without fancy progress bar"""
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
    
    # Make modules available globally
    globals().update({
        'sr': sr, 'sd': sd, 'sf': sf, 'torch': torch,
        'AutoTokenizer': AutoTokenizer, 'AutoModelForSequenceClassification': AutoModelForSequenceClassification,
        'TuyaOpenAPI': TuyaOpenAPI, 'string': string, 'json': json, 'Memory': Memory,
        'EnhancedMemory': EnhancedMemory, 'load_dotenv': load_dotenv, 'requests': requests, 'datetime': datetime,
        'asyncio': asyncio, 'ollama': ollama, 'np': np, 'threading': threading,
        'keyboard': keyboard, 'msvcrt': msvcrt, 'nltk': nltk, 'queue': queue, 're': re
    })

def supports_color():
    """Check if terminal supports ANSI colors."""
    if os.name == 'nt':
        try:
            import ctypes
            from ctypes import wintypes
            
            kernel32 = ctypes.windll.kernel32
            STD_OUTPUT_HANDLE = -11
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            
            handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            if handle == -1:
                return False
                
            mode = wintypes.DWORD()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                return False
                
            # Enable ANSI escape sequences
            new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
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
        if text_length > 1:
            ratio = i / (text_length - 1)
        else:
            ratio = 0
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
                # Found start of ANSI sequence, find the complete sequence
                escape_start = i
                i += 1
                # Skip through the escape sequence until we find the end
                while i < len(line) and line[i] != 'm':
                    i += 1
                if i < len(line):
                    i += 1  # Include the 'm'
                
                # Get the complete escape sequence
                escape_seq = line[escape_start:i]
                print(escape_seq, end="", flush=True)
                
                # Now get the next character (which should be the actual character)
                if i < len(line):
                    next_char = line[i]
                    print(next_char, end="", flush=True)
                    time.sleep(delay)
                    i += 1
            else:
                # Regular character without escape sequence
                print(char, end="", flush=True)
                time.sleep(delay)
                i += 1
        print()  # Add newline after each line

def strip_ansi_codes(text):
    """Remove ANSI color codes for length calculation."""
    ansi_escape = re.compile(r"\033\[[0-9;]*[mK]")
    return ansi_escape.sub("", text)

def initialize_and_run():
    """Initialize and run the M.I.T.S.U.H.A. AI assistant."""
    # Suppress transformers progress bars
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    # Load all modules with kawaii progress bar! ✨
    kawaii_import_modules()

    # Silence all future tqdm progress bars (e.g. from vectordb, GPT-SoVITS)
    try:
        import tqdm
        # Monkey-patch tqdm class to force disable=True by default
        # This affects all libraries that use tqdm (including pre-imported ones)
        if hasattr(tqdm, 'tqdm'):
            original_tqdm_init = tqdm.tqdm.__init__
            def new_tqdm_init(self, *args, **kwargs):
                kwargs['disable'] = True
                original_tqdm_init(self, *args, **kwargs)
            tqdm.tqdm.__init__ = new_tqdm_init
    except (ImportError, AttributeError):
        pass

    # Import the modules into local scope for this function
    global sr, sd, sf, torch, AutoTokenizer, AutoModelForSequenceClassification, TuyaOpenAPI
    global string, json, Memory, EnhancedMemory, load_dotenv, requests, datetime, asyncio, ollama, np
    global threading, keyboard, msvcrt, nltk, queue, re

    # Force enable colors for the terminal display
    supports_color()

    # Download required NLTK data
    with suppress_stdout_stderr():
        nltk.download("punkt_tab", quiet=True)

    # Enable CUDA optimizations
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

    # Load environment variables
    load_dotenv()

    # Import streaming inference module for TTS
    # Add required paths for GPT-SoVITS dependencies
    gpt_sovits_base = r"C:\Users\danu0\Downloads\OneReality\GPT-SoVITS-v2pro-20250604"
    sys.path.insert(0, gpt_sovits_base)
    sys.path.insert(0, os.path.join(gpt_sovits_base, "GPT_SoVITS"))
    sys.path.insert(0, os.path.join(gpt_sovits_base, "GPT_SoVITS", "eres2net"))
    
    with suppress_stdout_stderr():
        from streaming_inference import GPTSoVITSInference
        import streaming_tts_helpers

    # Initialize shared audio handler for animations
    global animation_handler
    animation_handler = None

    def audio_playback_thread(audio_queue: queue.Queue, sample_rate: int):
        """
        Enhanced audio playback thread that streams to Unity while playing locally for timing
        """
        global animation_handler
        # print(f"🎵 Audio playback thread starting with sample rate: {sample_rate}Hz")
        
        # Create dual audio player with correct server URL
        server_ip = os.getenv("IP_ADDRESS", "localhost")
        # print(f"🎵 Using server IP: {server_ip}")
        dual_player = create_mitsuha_audio_handler(
            server_url=f"http://{server_ip}:8000",
            local_volume=0.0  # Muted for timing only - Unity handles actual playback
        )
        
        # Make animation handler globally accessible
        animation_handler = dual_player
        
        dual_player.start_playback(sample_rate)
        
        try:
            fragment_num = 0
            while True:
                try:
                    # Get audio fragment from TTS generation queue
                    audio_fragment = audio_queue.get(timeout=1.0)
                    
                    if audio_fragment is None:  # Shutdown signal
                        break
                    
                    # Ensure proper data type
                    if audio_fragment.dtype != np.float32:
                        audio_fragment = audio_fragment.astype(np.float32)
                        
                    normalized_fragment = audio_fragment / 32768.0
                    
                    # Stream to Unity and play locally (muted) for timing
                    dual_player.add_audio_chunk(normalized_fragment)
                    
                    fragment_num += 1
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"❌ Audio playback error: {e}")
                    break
                    
        finally:
            dual_player.stop_playback()
            # print("🎵 Audio playback thread terminated")

    # Start server application
    os.system('start cmd /k "python app.py"')
    # os.startfile(r"server\dist\app\app.exe")
    upload_url = "http://" + os.getenv("IP_ADDRESS") + ":8000/uploaded_files/"
    
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

    text = ("Redefining Reality\n" f"[PROJECT M.I.T.S.U.H.A. CLOSED BETA]\n" + gradient_text("DogeLord", START_COLOR, END_COLOR))

    # Center text based on ASCII art width
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

    # Configuration
    tuya = os.getenv("USE_TUYA")
    lang_code = os.getenv("LANGUAGE")

    # Initialize enhanced conversation memory
    print(kawaii_gradient_text("🧠 Loading memories... ", "#FFB6C1", "#DDA0DD"), end="", flush=True)
    with suppress_stdout_stderr():
        base_memory = Memory()
        with open("conversation.jsonl", "r", encoding="utf-8") as f:
            conversation_data = [json.dumps(json.loads(line)) for line in f]
        base_memory.save(conversation_data)
        # Wrap with EnhancedMemory for smart retrieval
        memory = EnhancedMemory(base_memory, "conversation.jsonl")
    print(kawaii_gradient_text("✨ Done! ✨", "#90EE90", "#32CD32"))

    # Initialize speech-to-text recorder (voice mode only)
    recorder = None
    if not use_typing_mode:
        def on_recording_start():
            pass  # Silent operation

        def on_recording_stop():
            pass  # Silent operation

        def on_realtime_transcription_update(text):
            """Disabled - no streaming transcription to avoid incorrect intermediate results."""
            pass  # Disabled to prevent incorrect streaming transcriptions

        def preprocess_text(text):
            """Clean and format transcribed text."""
            text = text.lstrip()
            if text.startswith("..."):
                text = text[3:]
            text = text.lstrip()
            if text:
                text = text[0].upper() + text[1:]
            return text

        # Whisper model prompt for better conversation context
        initial_prompt = (
            "You are speaking with Mitsuha, an AI assistant. "
            "Add periods only for complete sentences. "
            "Use ellipsis (...) for unfinished thoughts or unclear endings. "
            "Examples:\n"
            "- Complete: 'Hello Mitsuha, how are you today?'\n"
            "- Incomplete: 'I was wondering if you could help me with...'\n"
            "- Conversation: 'Mitsuha, can you tell me about...'"
        )

        # Voice activity detection timing
        unknown_sentence_detection_pause = 0.7
        
        print(kawaii_gradient_text("🎤 Setting up voice recognition magic... ", "#FF69B4", "#DDA0DD"), end="", flush=True)
        with suppress_stdout_stderr():
            from RealtimeSTT import AudioToTextRecorder
            
            # Configure RealtimeSTT recorder
            recorder = AudioToTextRecorder(
                on_recording_start=on_recording_start,
                on_recording_stop=on_recording_stop,
                on_realtime_transcription_update=on_realtime_transcription_update,
                spinner=False,
                use_microphone=True,
                model=os.getenv("REALTIMESTT_MODEL"),
                realtime_model_type=os.getenv("REALTIMESTT_MODEL"),
                language=lang_code if lang_code else "en",
                silero_sensitivity=0.05,
                webrtc_sensitivity=3,
                post_speech_silence_duration=unknown_sentence_detection_pause,
                min_length_of_recording=1.1,
                min_gap_between_recordings=0,
                enable_realtime_transcription=False,  # Disabled to show only final transcription
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

    # Initialize GPT-SoVITS for voice synthesis
    print(kawaii_gradient_text("🎵 Preparing magical voice synthesis... ", "#FF69B4", "#FF1493"), end="", flush=True)
    try:
        # Reference audio configuration from environment
        ref_audio = os.getenv("GPT_SOVITS_REF_AUDIO")
        prompt_text = os.getenv("GPT_SOVITS_PROMPT_TEXT")
        
        # Initialize the streaming inference engine with suppressed output
        with suppress_stdout_stderr():
            MitsuTTS = GPTSoVITSInference(
                gpt_model_path=os.getenv("GPT_SOVITS_T2S_CKPT"),
                sovits_model_path=os.getenv("GPT_SOVITS_VITS_PTH")
            )
        
        print(kawaii_gradient_text("✨ Voice ready! ✨", "#90EE90", "#32CD32"))
        
    except Exception as e:
        print(kawaii_gradient_text("❌ Voice setup failed!", "#FF0000", "#8B0000"))
        print(f"Error loading GPT-SoVITS: {e}")
        print("Please check your GPT-SoVITS model paths")
        return

    # Configure Tuya smart home integration
    if tuya:
        ACCESS_ID = os.getenv("TUYA_ID")
        ACCESS_KEY = os.getenv("TUYA_SECRET")
        API_ENDPOINT = os.getenv("TUYA_ENDPOINT")

    # Initialize legacy speech recognition (unused but kept for compatibility)
    r = sr.Recognizer()
    mic = sr.Microphone()

    # Initialize NLI model for device control
    print(kawaii_gradient_text("🤖 Loading transformers... ", "#00CED1", "#1E90FF"), end="", flush=True)
    with suppress_stdout_stderr():
        tokenizer = AutoTokenizer.from_pretrained(os.getenv("NLI_RTE_TRANSFORMER"))
        model = AutoModelForSequenceClassification.from_pretrained(os.getenv("NLI_RTE_TRANSFORMER"))
    print(kawaii_gradient_text("✨ Transformers ready! ✨", "#90EE90", "#32CD32"))

    # Load system prompt for AI personality
    lore = os.getenv("LORE")
    lore = {"role": "system", "content": f"{lore}"}
    lore = json.dumps(lore)

    # Keyboard input handling
    def clear_input_buffer():
        """Clear any pending keyboard input."""
        while msvcrt.kbhit():
            msvcrt.getch()

    p_key_pressed = False

    def on_press(key):
        """Handle key press events."""
        nonlocal p_key_pressed
        try:
            if key.char == "p":
                p_key_pressed = True
        except AttributeError:
            pass

    def on_release(key):
        """Handle key release events."""
        nonlocal p_key_pressed
        try:
            if key.char == "p":
                p_key_pressed = False
        except AttributeError:
            pass

    # Message monitoring thread
    message = None

    def check_for_messages():
        """Monitor for external messages from server."""
        nonlocal message
        message = ""
        while True:
            try:
                with requests.Session() as session:
                    response = session.get(upload_url)
                    if response.status_code == 200:
                        data = json.loads(response.text)
                        if message != data.get("message"):
                            message = data.get("message")
            except Exception:
                pass
            time.sleep(0.5)

    def check_goodbye(transcript):
        """Check if user wants to end the conversation."""
        goodbye_words = ["bye", "goodbye", "see you"]
        # Use word tokenization to check for exact words
        tokens = nltk.word_tokenize(transcript.lower())
        return any(word in tokens for word in goodbye_words)

    # NLI functions for device control
    def test_entailment(text1, text2):
        """Test semantic entailment between two texts."""
        batch = tokenizer(text1, text2, return_tensors="pt").to(model.device)
        with suppress_stdout_stderr():
            with torch.no_grad():
                proba = torch.softmax(model(**batch).logits, -1)
        return proba.cpu().numpy()[0, model.config.label2id["ENTAILMENT"]]

    def test_equivalence(text1, text2):
        """Test semantic equivalence between two texts."""
        return test_entailment(text1, text2) * test_entailment(text2, text1)

    def replace_device(sentence, word):
        """Replace device placeholder in sentence."""
        return sentence.replace("[device]", word)

    def keep_sentence_with_word(text, word):
        """Extract sentences containing specific word."""
        sentences = re.split(r"[.,!?]", text)
        filtered_sentences = [
            sentence.strip() + punct
            for sentence, punct in zip(sentences, re.findall(r"[.,!?]", text))
            if word in sentence
        ]
        return " ".join(filtered_sentences)

    run_count = 0

    # Start keyboard listener for push-to-talk
    if not use_typing_mode:
        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()

    async def heart():
        """Main conversation loop."""
        nonlocal run_count, message
        session = requests.Session()

        while True:
            try:
                if use_typing_mode:
                    # Text input mode
                    print(kawaii_gradient_text("\nType your message to Mitsuha~ (or 'quit' to exit):", "#FFB6C1", "#DDA0DD"))
                    print(kawaii_gradient_text("You: ", "#00CED1", "#1E90FF"), end="", flush=True)
                    text = input().strip()

                    if text.lower() in ["quit", "exit", "bye", "goodbye"]:
                        break
                    if not text:
                        continue
                    trans = text
                else:
                    # Voice input mode
                    trans = ""

                    if push_to_talk:
                        print(kawaii_gradient_text("\nPress 'p' to speak with Mitsuha~", "#FF69B4", "#FF1493"))
                        while not p_key_pressed:
                            await asyncio.sleep(0.1)
                        print(kawaii_gradient_text("Listening... ", "#FFD700", "#FFA500"), end="", flush=True)

                        def process_complete_text(text):
                            nonlocal trans
                            text = preprocess_text(text)
                            trans = text
                            print()  # Add newline after completion

                        recorder.text(process_complete_text)
                    else:
                        print(kawaii_gradient_text("🎧 Always listening for you~ ", "#DDA0DD", "#9370DB"), end="", flush=True)

                        def process_complete_text(text):
                            nonlocal trans
                            text = preprocess_text(text)
                            trans = text
                            print()  # Add newline after completion

                        recorder.text(process_complete_text)

                    if not trans or len(trans.strip()) == 0:
                        print(kawaii_gradient_text("😔 No speech detected... Trying again~ ", "#FFA07A", "#FA8072"))
                        continue

                # Record timestamp
                now = datetime.now()
                date = now.strftime("%m/%d/%Y")
                time_2 = now.strftime("%H:%M:%S")

            except Exception as e:
                if not use_typing_mode:
                    # print(f"Error during audio capture: {e}")
                    # import traceback
                    # traceback.print_exc()
                    continue
                else:
                    continue

            text = trans
            # Remove "Mitsuha- " prefix if present
            if text.startswith("Mitsuha- "):
                text = text[9:]  # Remove first 9 characters ("Mitsuha- ")
            
            new_line = {
                "role": "user",
                "date": date,
                "time": time_2,
                "content": text,
            }

            # User input already displayed during input prompt (line 695)
            # No need to print again

            clear_input_buffer()

            # Save user message with importance metadata
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
                            # Continue with conversation even if smart home control fails
                            pass

            # Retrieve relevant conversation history with smart search
            query = f"""{text}"""
            current_time = datetime.now()
            
            # Check for repetitive queries
            with suppress_stdout_stderr():
                repetition_info = memory.detect_repetition(query, current_time, time_window_hours=24)
                
                # Get smart memory results (combines similarity + temporal + importance)
                smart_results = memory.search_smart(query, current_time, top_n=5)
            
            # Extract messages for context (backward compatible with old code)
            if len(smart_results) >= 2:
                line1 = smart_results[0]['chunk']
                line2 = smart_results[1]['chunk']
                line1_dict = json.loads(line1)
                line2_dict = json.loads(line2)
                line1_dict = json.dumps(line1_dict, separators=(",", ":"))
                line2_dict = json.dumps(line2_dict, separators=(",", ":"))
            else:
                # Fallback if not enough results
                line1 = json.dumps({"role": "system", "content": "No relevant memories"})
                line2 = line1
                line1_dict = line1
                line2_dict = line2

            # Build conversation context
            with open("conversation.jsonl", "r", encoding="UTF-8") as file:
                lines = [line.strip() for line in file.readlines()]

            if len(lines) >= 6:
                if run_count >= 3:
                    last_six_lines = "\n".join(lines[-6:])
                elif run_count == 0:
                    last_six_lines = line1 + "\n" + line2
                else:
                    last_six_lines = "\n".join(lines[-2 * run_count :])

                # Add relevant context from memory
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
                last_six_lines = "\n".join(lines)

            last_six_lines = [json.loads(line) for line in last_six_lines.split("\n")]
            
            # Clean timestamp prefixes from content for AI context
            cleaned_lines = []
            for line in last_six_lines:
                if "content" in line:
                    content = line["content"]
                    # Remove timestamp prefix pattern like "2023-09-24 / 17:56:37 / " from beginning
                    content = re.sub(r'^\d{4}-\d{2}-\d{2} / \d{2}:\d{2}:\d{2} / ', '', content)
                    content = re.sub(r'^\d{2}/\d{2}/\d{4} / \d{2}:\d{2}:\d{2} / ', '', content)
                    line["content"] = content
                cleaned_lines.append(line)
            
            # Note: User message already saved with metadata earlier

            # Prepare AI prompt with temporal context
            now = datetime.now()
            date = now.strftime("%m/%d/%Y")
            time_1 = now.strftime("%H:%M:%S")

            lore_dict = json.loads(lore)
            new_line_dict = json.loads(json.dumps(new_line))
            
            # Clean the new line content as well
            if "content" in new_line_dict:
                content = new_line_dict["content"]
                content = re.sub(r'^\d{4}-\d{2}-\d{2} / \d{2}:\d{2}:\d{2} / ', '', content)
                content = re.sub(r'^\d{2}/\d{2}/\d{4} / \d{2}:\d{2}:\d{2} / ', '', content)
                new_line_dict["content"] = content
            
            # Add temporal and repetition context to system message
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
            
            prompt = [lore_dict, *cleaned_lines, new_line_dict]

            # Emotion detection for animations - with variations
            emotion_hotkey_map = {
                "(wave)": "6",
                "(thumbs-up)": "7", 
                "(thumbs- up)": "7",  # Handle space variation
                "(nodding)": "8",
                "(shaking head)": "9",
                "(shaking- head)": "9",  # Handle space variation
                "(clap)": "10"
            }
            
            # Map emotions to animation names for Unity
            emotion_to_animation = {
                "(wave)": "Wave",
                "(thumbs-up)": "Thumbs-up", 
                "(thumbs- up)": "Thumbs-up",  # Handle space variation
                "(nodding)": "Nodding",
                "(shaking head)": "Shaking head",
                "(shaking- head)": "Shaking head",  # Handle space variation
                "(clap)": "Clap"
            }

            # Generate AI response
            print(kawaii_gradient_text("Mitsuha: ", "#FF69B4", "#DDA0DD"), end="")
            response = ""
            display_buffer = ""

            # Initialize concurrent TTS
            tts_queue = queue.Queue()
            audio_queue = queue.Queue()
            collected_fragments = []
            
            # Start playback thread immediately (assuming 32000Hz)
            playback_thread = threading.Thread(
                target=audio_playback_thread, args=(audio_queue, 32000)
            )
            playback_thread.start()
            
            # Start TTS worker thread
            tts_worker_thread = threading.Thread(
                target=streaming_tts_helpers.tts_worker,
                args=(tts_queue, audio_queue, MitsuTTS, ref_audio, prompt_text, collected_fragments),
                daemon=True
            )
            tts_worker_thread.start()
            
            sentence_buffer = ""

            for chunk in ollama.chat(model=os.getenv("LLM_MODEL"), messages=prompt, stream=True):
                chunk_content = chunk["message"]["content"]
                
                # Don't stop on newlines - let the model finish naturally
                # Only stop if done flag is set (ollama will handle this automatically)
                
                response += chunk_content
                display_buffer += chunk_content
                
                sentence_buffer += chunk_content
                
                # Check for sentence boundary
                if streaming_tts_helpers.detect_sentence_boundary(sentence_buffer):
                    # Clean and queue sentence
                    clean_sent = streaming_tts_helpers.clean_sentence_for_tts(sentence_buffer)
                    if clean_sent:
                        tts_queue.put(clean_sent)
                    sentence_buffer = ""
                
                # Process display buffer to filter out emotions
                while True:
                    # Find complete emotion patterns in buffer
                    emotion_found = False
                    for emotion in emotion_hotkey_map:
                        if emotion in display_buffer:
                            # Split by the emotion and display what's before it
                            parts = display_buffer.split(emotion, 1)
                            if parts[0]:  # Display text before emotion
                                pass
                                print(parts[0], end="", flush=True)
                            
                            # Send animation command to Unity if handler is available
                            if emotion in emotion_to_animation:
                                animation_name = emotion_to_animation[emotion]
                                if animation_handler:
                                    try:
                                        animation_handler.send_animation(animation_name)
                                    except Exception as e:
                                        pass
                                        # print(f"❌ Failed to send animation: {e}")
                                else:
                                    pass
                                    # print(f"⚠️ Animation handler not available yet")
                            
                            display_buffer = parts[1] if len(parts) > 1 else ""  # Keep what's after
                            emotion_found = True
                            break
                    
                    if not emotion_found:
                        # No complete emotions found, check if we can safely display some content
                        # Only display if buffer doesn't end with partial emotion patterns
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
            
            # Display any remaining buffer content (after filtering emotions)
            if display_buffer:
                # Final cleanup: remove any remaining gesture patterns with regex
                # This catches malformed patterns like "(-wave)", "(  )", etc.
                display_buffer = re.sub(r'\([^)]*(?:wave|thumbs|nod|shak|clap|  )[^)]*\)', '', display_buffer)
                # Also remove any standard emotion patterns that might have been missed
                for emotion in emotion_hotkey_map:
                    display_buffer = display_buffer.replace(emotion, "")
                if display_buffer.strip():  # Only print if there's actual content
                    print(display_buffer, end="", flush=True)
            
            print()

            # Save AI response with importance metadata
            new_line = {"role": "assistant", "date": date, "time": time_1, "content": response}
            with suppress_stdout_stderr():
                memory.save_with_metadata(new_line)

            # Process remaining buffer
            if sentence_buffer:
                clean_sent = streaming_tts_helpers.clean_sentence_for_tts(sentence_buffer)
                if clean_sent:
                    tts_queue.put(clean_sent)
            
            # Signal TTS worker to stop
            tts_queue.put(None)
            
            # Wait for TTS to finish
            tts_worker_thread.join()
            
            # Signal playback to stop
            audio_queue.put(None)
            playback_thread.join()

            # Determine filename based on emotions
            filename = "out.wav"
            for emotion, hotkey in emotion_hotkey_map.items():
                if emotion in response:
                    # Extract emotion name from parentheses: "(wave)" -> "wave"
                    emotion_name = emotion.strip("()")
                    filename = f"{emotion_name}.wav"
                    break

            # Concatenate fragments for file upload
            if collected_fragments:
                try:
                    full_audio = np.concatenate(collected_fragments)
                    # Normalize audio for saving (convert from raw float32 to [-1, 1] range)
                    normalized_audio = full_audio / 32768.0
                    
                    # Save to file
                    sf.write(filename, normalized_audio, 32000)
                    
                    # Upload audio file
                    with open(filename, "rb") as f:
                        files = {"file": (filename, f, "audio/wav")}
                        session.post(upload_url, files=files)
                except Exception as e:
                    pass
            else:
                # Fallback if no audio generated
                pass
            
            '''
            try:
                os.remove(filename)
            except Exception:
                pass
            '''
            run_count += 1

            if use_typing_mode:
                continue
            elif check_goodbye(trans):
                break

    # Main execution
    try:
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"

        # Start message monitoring thread
        t1 = threading.Thread(target=check_for_messages, daemon=True)
        t1.start()

        # Run main conversation loop
        asyncio.run(heart())

    except KeyboardInterrupt:
        print(kawaii_gradient_text("\n🌸 Mitsuha is going to sleep now... Goodbye! 🌸", "#FF69B4", "#DDA0DD"))
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(kawaii_gradient_text("✨ Shutting down gracefully... ✨", "#FFB6C1", "#DDA0DD"))

        # Cleanup threads and resources
        try:
            if 't1' in locals():
                t1.join(timeout=1.0)
        except:
            pass

        if not use_typing_mode and recorder is not None:
            try:
                recorder.shutdown()
                # print("🎤 Recorder shut down successfully.")
            except:
                pass

        if not use_typing_mode and 'listener' in locals():
            try:
                listener.stop()
            except:
                pass

        print(kawaii_gradient_text("💫 Application terminated. See you next time! 💫", "#FF1493", "#00CED1"))


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    initialize_and_run()
