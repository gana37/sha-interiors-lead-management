"""
voice_assistant.py - Voice Input (STT) and Text-to-Speech (TTS) Engine
SHA Interface Interiors - AI-Powered Interior Design Lead Management System

Features:
1. Text-to-Speech Sanitizer: Strips markdown, emojis, asterisks, tables, and URLs for natural English speech.
2. HTML5 Web Speech API Bridges for Streamlit:
   - Voice Input (Speech-to-Text) with live microphone capture, multilingual support, and copy/apply action.
   - Text-to-Speech Audio Player with Play, Pause/Stop, and Replay controls.
3. Voice Transcription Pipeline: Enriches audio transcripts with language detection and internal English translation.
4. Mandatory Rule: TTS audio is always read aloud in clean, professional ENGLISH ONLY.
"""

import os
import re
import html
import json
from typing import Dict, Any, Optional
import multilingual_engine


def clean_text_for_speech(raw_text: str) -> str:
    """
    Sanitizes markdown, URLs, tables, emojis, and symbols into clean,
    fluent, conversational English text suitable for speech synthesis.
    """
    if not raw_text:
        return ""

    text = raw_text

    # 1. Replace specific SHA URLs with natural spoken equivalents
    text = re.sub(
        r'https://calendar\.app\.google/[^\s\)\>]+',
        'at the Google Calendar booking link provided',
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r'https://maps\.app\.goo\.gl/[^\s\)\>]+',
        'at our Miyapur office Google Maps location',
        text,
        flags=re.IGNORECASE
    )
    # Generic URLs
    text = re.sub(r'https?://\S+', 'link', text)

    # 2. Handle Markdown tables: extract cell contents into commas/sentences
    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and stripped.endswith('|'):
            # Check if it's a separator line (e.g., |---|---|)
            if re.match(r'^\|[\s\-:\|]+\|$', stripped):
                continue
            # Extract cells
            cells = [c.strip() for c in stripped.strip('|').split('|') if c.strip()]
            if cells:
                processed_lines.append(". ".join(cells) + ".")
        else:
            processed_lines.append(line)
    text = "\n".join(processed_lines)

    # 3. Strip Markdown headers (### Header -> Header)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)

    # 4. Strip Markdown blockquotes and callouts (> [!NOTE])
    text = re.sub(r'^\s*>\s*(\[!.*?\])?\s*', '', text, flags=re.MULTILINE)

    # 5. Strip bullet markers (- item, * item, 1. item) BEFORE inline asterisks
    text = re.sub(r'^\s*[\*\-\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # 6. Strip backticks (code snippets)
    text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text, flags=re.DOTALL)

    # 7. Strip Markdown bold/italic (*, **)
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}(.*?)_{1,3}', r'\1', text)
    text = text.replace('*', '').replace('_', '')

    # 8. Remove common emojis using unicode ranges
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended
        "\U00002600-\U000026FF"  # misc symbols
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)

    # 9. Clean up multiple whitespaces, newlines, and punctuation artifacts
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'\s*([,\.\?!])', r'\1', text)
    text = re.sub(r'([,\.\?!]){2,}', r'\1', text)

    return text.strip()


def process_voice_transcription(
    transcription_text: str,
    explicit_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Processes spoken audio text from voice input.
    Detects language, translates to English internally, and preserves technical terms.
    """
    clean_transcript = transcription_text.strip()
    if not clean_transcript:
        return {
            "transcription": "",
            "language_code": "en",
            "language_name": "English",
            "english_translation": "",
            "is_flagged_for_review": False,
            "preserved_terms": []
        }

    processed = multilingual_engine.process_customer_message(clean_transcript)
    if explicit_language:
        processed["language_code"] = explicit_language

    return {
        "transcription": clean_transcript,
        "language_code": processed["language_code"],
        "language_name": processed["language_name"],
        "is_transliterated": processed["is_transliterated"],
        "english_translation": processed["english_translation"],
        "is_flagged_for_review": processed["is_flagged_for_review"],
        "preserved_terms": processed["technical_terms_preserved"]
    }


def get_tts_html_snippet(
    text: str,
    snippet_id: str = "tts_player_0",
    autoplay: bool = False
) -> str:
    """
    Generates an HTML/JS widget for the browser's native Web Speech API (speechSynthesis).
    Provides AI voice output with Listen, Stop, and Replay controls.
    Spoken in clean, professional English only.
    """
    spoken_text = clean_text_for_speech(text)
    escaped_text = html.escape(spoken_text)
    js_text = json.dumps(spoken_text)

    html_code = f"""
    <div id="{snippet_id}_container" style="display:inline-flex; align-items:center; gap:6px; margin: 4px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <button id="{snippet_id}_btn_play" onclick="speak_{snippet_id}()" title="Read Aloud (English)" style="background:#2563EB; color:white; border:none; border-radius:14px; padding:4px 11px; font-size:12px; font-weight:600; cursor:pointer; display:inline-flex; align-items:center; gap:4px; box-shadow: 0 1px 2px rgba(0,0,0,0.06); transition: all 0.15s ease;">
            <span>🔊 Listen</span>
        </button>
        <button id="{snippet_id}_btn_stop" onclick="stop_{snippet_id}()" title="Stop Voice Output" style="background:#EF4444; color:white; border:none; border-radius:14px; padding:4px 11px; font-size:12px; font-weight:600; cursor:pointer; display:none; align-items:center; gap:4px; box-shadow: 0 1px 2px rgba(0,0,0,0.06); transition: all 0.15s ease;">
            <span>⏹ Stop</span>
        </button>
        <button id="{snippet_id}_btn_replay" onclick="replay_{snippet_id}()" title="Replay from beginning" style="background:#475569; color:white; border:none; border-radius:14px; padding:4px 11px; font-size:12px; font-weight:600; cursor:pointer; display:none; align-items:center; gap:4px; box-shadow: 0 1px 2px rgba(0,0,0,0.06); transition: all 0.15s ease;">
            <span>🔄 Replay</span>
        </button>
        <span id="{snippet_id}_status" style="font-size:11px; color:#6B7280; font-weight:500;"></span>
    </div>

    <script>
    (function() {{
        var text = {js_text};
        var isSpeaking = false;
        var synth = window.speechSynthesis;

        window.speak_{snippet_id} = function() {{
            if (!('speechSynthesis' in window)) {{
                alert('Speech synthesis is not supported in this browser.');
                return;
            }}

            if (synth.speaking) {{
                synth.cancel();
            }}

            var utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'en-US';
            utterance.rate = 1.0;
            utterance.pitch = 1.0;

            // Pick a good English voice if available
            var voices = synth.getVoices();
            for (var i = 0; i < voices.length; i++) {{
                if (voices[i].lang.startsWith('en') && (voices[i].name.includes('Natural') || voices[i].name.includes('Google') || voices[i].name.includes('Samantha') || voices[i].name.includes('Microsoft'))) {{
                    utterance.voice = voices[i];
                    break;
                }}
            }}

            var playBtn = document.getElementById('{snippet_id}_btn_play');
            var stopBtn = document.getElementById('{snippet_id}_btn_stop');
            var replayBtn = document.getElementById('{snippet_id}_btn_replay');
            var statusSpan = document.getElementById('{snippet_id}_status');

            utterance.onstart = function() {{
                isSpeaking = true;
                playBtn.style.display = 'none';
                stopBtn.style.display = 'inline-flex';
                replayBtn.style.display = 'none';
                statusSpan.innerText = 'Speaking...';
            }};

            utterance.onend = function() {{
                isSpeaking = false;
                playBtn.style.display = 'none';
                stopBtn.style.display = 'none';
                replayBtn.style.display = 'inline-flex';
                statusSpan.innerText = '';
            }};

            utterance.onerror = function() {{
                isSpeaking = false;
                playBtn.style.display = 'inline-flex';
                stopBtn.style.display = 'none';
                replayBtn.style.display = 'none';
                statusSpan.innerText = '';
            }};

            synth.speak(utterance);
        }};

        window.stop_{snippet_id} = function() {{
            if (synth) {{
                synth.cancel();
            }}
            isSpeaking = false;
            document.getElementById('{snippet_id}_btn_play').style.display = 'none';
            document.getElementById('{snippet_id}_btn_stop').style.display = 'none';
            document.getElementById('{snippet_id}_btn_replay').style.display = 'inline-flex';
            document.getElementById('{snippet_id}_status').innerText = '';
        }};

        window.replay_{snippet_id} = function() {{
            window.speak_{snippet_id}();
        }};

        {'speak_' + snippet_id + '();' if autoplay else ''}
    }})();
    </script>
    """
    return html_code


def get_voice_input_html_snippet(
    container_id: str = "voice_stt_input"
) -> str:
    """
    Generates an HTML/JS widget for the browser's native Web Speech API (webkitSpeechRecognition).
    Captures live microphone audio, supports Indian languages & English, displays live transcript,
    and provides a 1-click Copy button to transfer text directly into Streamlit.
    """
    return f"""
    <div id="{container_id}_box" style="border:1px solid #E5E7EB; border-radius:8px; padding:12px 14px; background:#F9FAFB; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin-bottom: 12px;">
        <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
            <div style="display:flex; align-items:center; gap:8px;">
                <button id="{container_id}_mic_btn" onclick="toggleVoiceInput_{container_id}()" style="background:#10B981; color:white; border:none; border-radius:6px; padding:7px 14px; font-size:13px; font-weight:600; cursor:pointer; display:inline-flex; align-items:center; gap:6px;">
                    <span id="{container_id}_mic_icon">🎤</span> <span id="{container_id}_btn_text">Start Voice Input</span>
                </button>
                <select id="{container_id}_lang" style="padding:6px 10px; border-radius:6px; border:1px solid #D1D5DB; font-size:12px; background:white;">
                    <option value="en-IN" selected>English (India)</option>
                    <option value="te-IN">Telugu (తెలుగు)</option>
                    <option value="hi-IN">Hindi (हिन्दी)</option>
                    <option value="ta-IN">Tamil (தமிழ்)</option>
                    <option value="kn-IN">Kannada (ಕನ್ನಡ)</option>
                    <option value="ml-IN">Malayalam (മലയാളം)</option>
                    <option value="mr-IN">Marathi (मराठी)</option>
                    <option value="bn-IN">Bengali (বাংলা)</option>
                    <option value="gu-IN">Gujarati (ગુજરાતી)</option>
                    <option value="pa-IN">Punjabi (ਪੰਜਾਬੀ)</option>
                    <option value="ur-IN">Urdu (اردو)</option>
                </select>
            </div>
            <span id="{container_id}_status" style="font-size:12px; font-weight:500; color:#6B7280;">Ready</span>
        </div>

        <div id="{container_id}_transcript_box" style="margin-top:10px; min-height:48px; max-height:120px; overflow-y:auto; background:white; border:1px solid #D1D5DB; border-radius:6px; padding:8px 10px; font-size:13px; color:#1F2937; line-height:1.4;">
            <em style="color:#9CA3AF;">Your spoken voice transcription will appear here in real-time...</em>
        </div>

        <div style="margin-top:8px; display:flex; justify-content:flex-end; gap:8px;">
            <button id="{container_id}_copy_btn" onclick="copyTranscript_{container_id}()" style="background:#4B5563; color:white; border:none; border-radius:5px; padding:5px 12px; font-size:12px; cursor:pointer;">
                📋 Copy Transcript
            </button>
            <button id="{container_id}_clear_btn" onclick="clearTranscript_{container_id}()" style="background:#9CA3AF; color:white; border:none; border-radius:5px; padding:5px 10px; font-size:12px; cursor:pointer;">
                Clear
            </button>
        </div>
    </div>

    <script>
    (function() {{
        var recognition = null;
        var isListening = false;
        var finalTranscript = '';

        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        window.toggleVoiceInput_{container_id} = function() {{
            if (!SpeechRecognition) {{
                alert('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
                return;
            }}

            if (isListening) {{
                if (recognition) recognition.stop();
                return;
            }}

            recognition = new SpeechRecognition();
            var langSelect = document.getElementById('{container_id}_lang');
            recognition.lang = langSelect.value;
            recognition.continuous = true;
            recognition.interimResults = true;

            var micBtn = document.getElementById('{container_id}_mic_btn');
            var btnText = document.getElementById('{container_id}_btn_text');
            var status = document.getElementById('{container_id}_status');
            var transcriptBox = document.getElementById('{container_id}_transcript_box');

            recognition.onstart = function() {{
                isListening = true;
                micBtn.style.background = '#EF4444';
                btnText.innerText = 'Stop Listening';
                status.innerText = '🔴 Listening...';
                status.style.color = '#EF4444';
            }};

            recognition.onresult = function(event) {{
                var interimTranscript = '';
                for (var i = event.resultIndex; i < event.results.length; ++i) {{
                    if (event.results[i].isFinal) {{
                        finalTranscript += event.results[i][0].transcript + ' ';
                    }} else {{
                        interimTranscript += event.results[i][0].transcript;
                    }}
                }}
                transcriptBox.innerText = finalTranscript + interimTranscript;
            }};

            recognition.onerror = function(event) {{
                console.error('Speech recognition error:', event.error);
                status.innerText = 'Error: ' + event.error;
                status.style.color = '#DC2626';
            }};

            recognition.onend = function() {{
                isListening = false;
                micBtn.style.background = '#10B981';
                btnText.innerText = 'Start Voice Input';
                status.innerText = 'Finished';
                status.style.color = '#10B981';
            }};

            recognition.start();
        }};

        window.copyTranscript_{container_id} = function() {{
            var transcriptBox = document.getElementById('{container_id}_transcript_box');
            var text = transcriptBox.innerText;
            if (text && !text.includes('Your spoken voice transcription')) {{
                navigator.clipboard.writeText(text).then(function() {{
                    alert('Transcript copied to clipboard! You can paste it into the AI chat input.');
                }});
            }}
        }};

        window.clearTranscript_{container_id} = function() {{
            finalTranscript = '';
            document.getElementById('{container_id}_transcript_box').innerHTML = '<em style="color:#9CA3AF;">Your spoken voice transcription will appear here in real-time...</em>';
            document.getElementById('{container_id}_status').innerText = 'Ready';
        }};
    }})();
    </script>
    """


def get_unified_chat_composer_bridge() -> str:
    """
    Generates an HTML/JS bridge component that connects the browser's Web Speech API
    directly into Streamlit's stChatInput DOM element.

    Features:
    1. Unified Composer: Injects an inline microphone button and a multilingual
       language dropdown directly inside the main chat input bar beside the Send button.
    2. Rounded Styling: Polishes the chat input bar with ChatGPT-inspired rounded styling (28px radius,
       modern border and elevation shadow).
    3. Multilingual Speech Recognition: Supports English (en-IN), Telugu (te-IN), Hindi (hi-IN),
       Tamil (ta-IN), Kannada (kn-IN), Malayalam (ml-IN), Marathi (mr-IN), Bengali (bn-IN).
    4. Active Listening Feedback: Visual red pulsing halo and state changes while the mic is active.
    5. STRICT NO-AUTO-SEND RULE: Recognized speech is transcribed directly into the editable
       textarea for user review and editing. It is NEVER submitted automatically!
       Submission only occurs when the user explicitly clicks the Send button or presses Enter.
    6. Resilience & State Persistence: Language selection is persisted across Streamlit reruns.
    """
    return """
    <div id="sha_voice_bridge_meta" style="display:none;" data-version="2.1"></div>
    <script>
    (function() {
        var PARENT_DOC = (window.parent && window.parent.document) ? window.parent.document : document;
        var PARENT_WIN = (window.parent && window.parent.window) ? window.parent.window : window;

        // Ensure iframe permission attribute
        try {
            if (window.frameElement) {
                window.frameElement.setAttribute('allow', 'microphone; speech-recognition');
            }
        } catch (e) {}

        // 1. Inject modern ChatGPT-style CSS and layout fixes into parent head
        var styleId = 'sha_chat_input_styles';
        var styleEl = PARENT_DOC.getElementById(styleId);
        if (!styleEl) {
            styleEl = PARENT_DOC.createElement('style');
            styleEl.id = styleId;
            PARENT_DOC.head.appendChild(styleEl);
        }
        styleEl.textContent = `
            [data-testid="stChatInput"] {
                border-radius: 28px !important;
                border: 1.5px solid #CBD5E1 !important;
                background-color: #FFFFFF !important;
                box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08) !important;
                transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
                padding-right: 6px !important;
            }
            [data-testid="stChatInput"]:focus-within {
                border-color: #2563EB !important;
                box-shadow: 0 4px 20px rgba(37, 99, 235, 0.16) !important;
            }
            /* Ensure textarea wrapper does not overlap the voice controls */
            [data-testid="stChatInput"] [data-baseweb="textarea"] {
                margin-right: 215px !important;
            }
            [data-testid="stChatInputTextArea"] {
                font-size: 14.5px !important;
                line-height: 1.5 !important;
                color: #0F172A !important;
            }
            /* Crucial: Ensure the button container and injected controls have full pointer events and top stacking context */
            [data-testid="stChatInput"] div:has(> button[data-testid="stChatInputSubmitButton"]),
            [data-testid="stChatInput"] .st-emotion-cache-sey4o0 {
                pointer-events: auto !important;
                z-index: 9999 !important;
                position: absolute !important;
                right: 8px !important;
                bottom: 6px !important;
            }
            .sha-voice-controls {
                display: inline-flex !important;
                align-items: center !important;
                gap: 6px !important;
                margin-right: 6px !important;
                vertical-align: middle !important;
                position: relative !important;
                z-index: 10000 !important;
                pointer-events: auto !important;
            }
            .sha-lang-select {
                background: #F1F5F9 !important;
                border: 1px solid #CBD5E1 !important;
                border-radius: 14px !important;
                padding: 4px 8px !important;
                font-size: 11px !important;
                font-weight: 600 !important;
                color: #334155 !important;
                cursor: pointer !important;
                height: 30px !important;
                outline: none !important;
                position: relative !important;
                z-index: 101 !important;
                pointer-events: auto !important;
                transition: all 0.15s ease !important;
            }
            .sha-lang-select:hover {
                background: #E2E8F0 !important;
                border-color: #94A3B8 !important;
            }
            .sha-mic-button {
                background: #F1F5F9 !important;
                border: 1px solid #CBD5E1 !important;
                border-radius: 50% !important;
                width: 32px !important;
                height: 32px !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                cursor: pointer !important;
                position: relative !important;
                z-index: 101 !important;
                pointer-events: auto !important;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
                padding: 0 !important;
            }
            .sha-mic-button:hover {
                background: #E2E8F0 !important;
                border-color: #94A3B8 !important;
                transform: scale(1.05) !important;
            }
            .sha-mic-button.listening {
                background: #EF4444 !important;
                border-color: #DC2626 !important;
                box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7) !important;
                animation: sha-pulse-ring 1.4s cubic-bezier(0.24, 0, 0.38, 1) infinite !important;
            }
            .sha-mic-button.listening svg {
                stroke: #FFFFFF !important;
            }
            @keyframes sha-pulse-ring {
                0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
                70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
                100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
            }
            .sha-voice-toast {
                position: fixed;
                bottom: 84px;
                right: 28px;
                background: #0F172A;
                color: #FFFFFF;
                padding: 10px 16px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                box-shadow: 0 8px 24px rgba(0,0,0,0.2);
                z-index: 999999;
                display: flex;
                align-items: center;
                gap: 8px;
                animation: shaFadeIn 0.2s ease;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            @keyframes shaFadeIn {
                from { opacity: 0; transform: translateY(8px); }
                to { opacity: 1; transform: translateY(0); }
            }
        `;

        function showVoiceToast(msg, isError) {
            var existing = PARENT_DOC.getElementById('sha_voice_toast');
            if (existing) existing.remove();

            var toast = PARENT_DOC.createElement('div');
            toast.id = 'sha_voice_toast';
            toast.className = 'sha-voice-toast';
            if (isError) {
                toast.style.background = '#DC2626';
            }
            toast.innerHTML = (isError ? '⚠️ ' : 'ℹ️ ') + msg;
            PARENT_DOC.body.appendChild(toast);
            setTimeout(function() {
                if (toast && toast.parentElement) toast.remove();
            }, 4500);
        }

        function injectUnifiedComposer() {
            var chatInput = PARENT_DOC.querySelector('[data-testid="stChatInput"]');
            if (!chatInput) return false;

            var textarea = chatInput.querySelector('textarea[data-testid="stChatInputTextArea"]');
            var submitBtn = chatInput.querySelector('button[data-testid="stChatInputSubmitButton"]');
            if (!textarea || !submitBtn) return false;

            var btnContainer = submitBtn.parentElement;
            if (!btnContainer) return false;

            // Ensure baseWeb container does not overlap
            var baseWebContainer = textarea.closest('[data-baseweb="textarea"]');
            if (baseWebContainer) {
                baseWebContainer.style.setProperty('margin-right', '215px', 'important');
            }

            btnContainer.style.setProperty('pointer-events', 'auto', 'important');
            btnContainer.style.setProperty('z-index', '9999', 'important');
            btnContainer.style.setProperty('position', 'absolute', 'important');
            btnContainer.style.setProperty('right', '8px', 'important');
            btnContainer.style.setProperty('bottom', '6px', 'important');

            // Check if already injected in this container
            var existing = PARENT_DOC.getElementById('sha_voice_composer_container');
            if (existing && btnContainer.contains(existing)) {
                return true;
            }
            if (existing && !btnContainer.contains(existing)) {
                existing.remove();
            }

            var controlsDiv = PARENT_DOC.createElement('div');
            controlsDiv.id = 'sha_voice_composer_container';
            controlsDiv.className = 'sha-voice-controls';
            controlsDiv.style.setProperty('pointer-events', 'auto', 'important');
            controlsDiv.style.setProperty('z-index', '10000', 'important');
            controlsDiv.style.setProperty('display', 'inline-flex', 'important');
            controlsDiv.style.setProperty('align-items', 'center', 'important');

            // Language dropdown
            var langSelect = PARENT_DOC.createElement('select');
            langSelect.id = 'sha_voice_lang';
            langSelect.className = 'sha-lang-select';
            langSelect.title = 'Voice Language Selection';
            langSelect.style.setProperty('pointer-events', 'auto', 'important');
            langSelect.style.setProperty('z-index', '10001', 'important');

            var langs = [
                { c: 'en-IN', l: '🌐 EN (India)' },
                { c: 'te-IN', l: 'TE (తెలుగు)' },
                { c: 'hi-IN', l: 'HI (हिन्दी)' },
                { c: 'ta-IN', l: 'TA (தமிழ்)' },
                { c: 'kn-IN', l: 'KN (ಕನ್ನಡ)' },
                { c: 'ml-IN', l: 'ML (മലയാളം)' },
                { c: 'mr-IN', l: 'MR (मराठी)' },
                { c: 'bn-IN', l: 'BN (বাংলা)' }
            ];

            var savedLang = 'en-IN';
            try {
                if (PARENT_WIN.sessionStorage && PARENT_WIN.sessionStorage.getItem('sha_voice_lang')) {
                    savedLang = PARENT_WIN.sessionStorage.getItem('sha_voice_lang');
                } else if (PARENT_WIN.sha_selected_voice_lang) {
                    savedLang = PARENT_WIN.sha_selected_voice_lang;
                }
            } catch (e) {}

            langs.forEach(function(item) {
                var opt = PARENT_DOC.createElement('option');
                opt.value = item.c;
                opt.textContent = item.l;
                if (item.c === savedLang) {
                    opt.selected = true;
                }
                langSelect.appendChild(opt);
            });

            // Microphone icon button
            var micBtn = PARENT_DOC.createElement('button');
            micBtn.id = 'sha_voice_mic_btn';
            micBtn.type = 'button';
            micBtn.className = 'sha-mic-button';
            micBtn.style.setProperty('pointer-events', 'auto', 'important');
            micBtn.style.setProperty('z-index', '10001', 'important');
            micBtn.title = 'Speak your question (Multilingual voice typing)';
            micBtn.innerHTML = `
                <svg id="sha_mic_svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="pointer-events:none;">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="23"></line>
                    <line x1="8" y1="23" x2="16" y2="23"></line>
                </svg>
            `;

            controlsDiv.appendChild(langSelect);
            controlsDiv.appendChild(micBtn);
            btnContainer.insertBefore(controlsDiv, submitBtn);

            // Prevent event stealing by textarea
            [langSelect, micBtn].forEach(function(el) {
                el.addEventListener('mousedown', function(e) { e.stopPropagation(); });
                el.addEventListener('pointerdown', function(e) { e.stopPropagation(); });
                el.addEventListener('touchstart', function(e) { e.stopPropagation(); });
            });

            // Sync with Streamlit React state
            function setReactInputValue(val) {
                var nativeSetter = Object.getOwnPropertyDescriptor(
                    PARENT_WIN.HTMLTextAreaElement.prototype,
                    "value"
                ) ? Object.getOwnPropertyDescriptor(
                    PARENT_WIN.HTMLTextAreaElement.prototype,
                    "value"
                ).set : null;

                if (nativeSetter) {
                    nativeSetter.call(textarea, val);
                } else {
                    textarea.value = val;
                }
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                textarea.dispatchEvent(new Event('change', { bubbles: true }));
            }

            // Web Speech API Integration
            var SpeechRecognition = PARENT_WIN.SpeechRecognition ||
                                   PARENT_WIN.webkitSpeechRecognition ||
                                   window.SpeechRecognition ||
                                   window.webkitSpeechRecognition;

            var recognition = PARENT_WIN.sha_active_recognition || null;
            var isListening = false;
            var baseText = "";

            langSelect.addEventListener('change', function(e) {
                e.stopPropagation();
                var newLang = langSelect.value;
                try {
                    if (PARENT_WIN.sessionStorage) {
                        PARENT_WIN.sessionStorage.setItem('sha_voice_lang', newLang);
                    }
                    PARENT_WIN.sha_selected_voice_lang = newLang;
                } catch (err) {}

                if (isListening && recognition) {
                    try {
                        recognition.lang = newLang;
                    } catch (err) {}
                }
            });

            micBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();

                if (!SpeechRecognition) {
                    showVoiceToast('Speech recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge.', true);
                    return;
                }

                if (isListening) {
                    if (recognition) {
                        try { recognition.abort(); } catch (err) {}
                    }
                    isListening = false;
                    micBtn.classList.remove('listening');
                    micBtn.title = 'Speak your question (Multilingual voice typing)';
                    return;
                }

                if (PARENT_WIN.sha_active_recognition) {
                    try { PARENT_WIN.sha_active_recognition.abort(); } catch (e) {}
                }

                try {
                    recognition = new SpeechRecognition();
                    PARENT_WIN.sha_active_recognition = recognition;
                } catch (err) {
                    showVoiceToast('Could not initialize Speech Recognition: ' + err.message, true);
                    return;
                }

                var chosenLang = langSelect.value || 'en-IN';
                recognition.lang = chosenLang;
                recognition.continuous = true;
                recognition.interimResults = true;

                // Capture initial text in the input
                baseText = textarea.value || "";
                if (baseText.length > 0 && !baseText.endsWith(" ")) {
                    baseText += " ";
                }

                recognition.onstart = function() {
                    isListening = true;
                    micBtn.classList.add('listening');
                    var langLabel = langSelect.options[langSelect.selectedIndex] ? langSelect.options[langSelect.selectedIndex].text : chosenLang;
                    micBtn.title = '🔴 Listening (' + langLabel + ')... Click to stop';
                    showVoiceToast('🎤 Listening (' + langLabel + ')... Speak now.', false);
                };

                recognition.onresult = function(evt) {
                    var finalPart = "";
                    var interimPart = "";
                    for (var i = evt.resultIndex; i < evt.results.length; ++i) {
                        if (evt.results[i].isFinal) {
                            finalPart += evt.results[i][0].transcript + " ";
                        } else {
                            interimPart += evt.results[i][0].transcript;
                        }
                    }
                    if (finalPart) {
                        baseText += finalPart;
                    }
                    var combinedText = (baseText + interimPart).trimStart();
                    // DIRECT EDITABLE PLACEMENT - STRICT NO-AUTO-SEND RULE
                    setReactInputValue(combinedText);
                };

                recognition.onerror = function(evt) {
                    console.warn('Speech recognition error:', evt.error);
                    isListening = false;
                    micBtn.classList.remove('listening');
                    micBtn.title = 'Speak your question (Multilingual voice typing)';

                    if (evt.error === 'not-allowed') {
                        showVoiceToast('Microphone access denied. Please allow microphone permissions in your browser URL bar to use voice input.', true);
                    } else if (evt.error === 'network') {
                        showVoiceToast('Speech recognition network error. Please check your internet connection.', true);
                    } else if (evt.error === 'no-speech') {
                        // Silent timeout
                    } else if (evt.error !== 'aborted') {
                        showVoiceToast('Speech recognition error: ' + evt.error, true);
                    }
                };

                recognition.onend = function() {
                    isListening = false;
                    micBtn.classList.remove('listening');
                    micBtn.title = 'Speak your question (Multilingual voice typing)';
                };

                try {
                    recognition.start();
                } catch (err) {
                    console.warn('Recognition start exception:', err);
                    if (err.name === 'InvalidStateError') {
                        try { recognition.stop(); } catch (e) {}
                        isListening = false;
                        micBtn.classList.remove('listening');
                    } else {
                        showVoiceToast('Microphone error: ' + err.message, true);
                    }
                }
            });

            return true;
        }

        // Retry until chat input is rendered
        injectUnifiedComposer();
        var attempts = 0;
        var timer = setInterval(function() {
            attempts++;
            if (injectUnifiedComposer() || attempts > 50) {
                clearInterval(timer);
            }
        }, 150);

        // Reactivity observer for Streamlit re-renders
        try {
            if (!PARENT_WIN.sha_composer_observer) {
                var observer = new MutationObserver(function() {
                    var chatInput = PARENT_DOC.querySelector('[data-testid="stChatInput"]');
                    var mic = PARENT_DOC.getElementById('sha_voice_mic_btn');
                    if (chatInput && !mic) {
                        injectUnifiedComposer();
                    }
                });
                observer.observe(PARENT_DOC.body, { childList: true, subtree: true });
                PARENT_WIN.sha_composer_observer = observer;
            }
        } catch (e) {
            console.warn('Could not attach MutationObserver:', e);
        }
    })();
    </script>
    """
