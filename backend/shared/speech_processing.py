"""
Speech Processing Module for AI Interview System

This module combines speech-to-text (STT) and text-to-speech (TTS) functionality:
- Speech recognition using Whisper (faster-whisper)
- Text-to-speech generation using Kokoro TTS
- Audio recording and playback utilities

Used primarily by the oral interview module for voice-based interactions.
"""

import wave
import pyaudio
import numpy as np
import tempfile
import os
from faster_whisper import WhisperModel
from kokoro import KPipeline
import soundfile as sf
from typing import Optional


# ============================================================================
# Speech-to-Text (STT) Functions
# ============================================================================

# Global STT model instance
_whisper_model: Optional[WhisperModel] = None


def initialize_whisper_model(model_name: str = "base.en", device: str = "cpu",
                             compute_type: str = "int8") -> Optional[WhisperModel]:
    """
    Initialize the Whisper model for speech recognition

    Args:
        model_name: Whisper model size (tiny, base, small, medium, large)
        device: Device to run on ("cpu" or "cuda")
        compute_type: Compute precision ("int8", "float16", "float32")

    Returns:
        WhisperModel instance or None if initialization fails
    """
    global _whisper_model
    try:
        _whisper_model = WhisperModel(model_name, device=device, compute_type=compute_type)
        print(f"✅ Speech recognition model initialized: {model_name}")
        return _whisper_model
    except Exception as e:
        print(f"❌ Error initializing speech recognition model: {e}")
        return None


def get_whisper_model() -> Optional[WhisperModel]:
    """
    Get the global Whisper model instance, initializing if needed

    Returns:
        WhisperModel instance or None
    """
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = initialize_whisper_model()
    return _whisper_model


def record_audio(duration: int = 30, sample_rate: int = 16000) -> str:
    """
    Record audio from microphone for a specified duration

    Args:
        duration: Recording duration in seconds (default: 30)
        sample_rate: Audio sample rate in Hz (default: 16000)

    Returns:
        str: Path to the temporary WAV file containing the recording
    """
    print(f"\n🎤 Listening... Speak your answer (recording for {duration} seconds)")

    # PyAudio configuration
    chunk = 1024
    audio_format = pyaudio.paInt16
    channels = 1

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open stream
    stream = p.open(
        format=audio_format,
        channels=channels,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk
    )

    # Record audio
    frames = []
    for i in range(0, int(sample_rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    print("✅ Recording complete!")

    # Save as temporary WAV file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_filename = temp_file.name
    temp_file.close()

    wf = wave.open(temp_filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(audio_format))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    return temp_filename


def transcribe_audio(audio_file: str, model: Optional[WhisperModel] = None,
                     cleanup: bool = True) -> str:
    """
    Transcribe audio file using Whisper model

    Args:
        audio_file: Path to audio file
        model: Whisper model instance (uses global if None)
        cleanup: Whether to delete the audio file after transcription

    Returns:
        str: Transcribed text or empty string if transcription fails
    """
    if model is None:
        model = get_whisper_model()

    if model is None:
        print("❌ Whisper model not available")
        return ""

    try:
        # Transcribe the audio file
        segments, info = model.transcribe(audio_file, beam_size=5)

        # Combine all segments into a single text
        transcript = ""
        for segment in segments:
            transcript += segment.text + " "

        # Clean up the temporary file if requested
        if cleanup and os.path.exists(audio_file):
            os.unlink(audio_file)

        return transcript.strip()
    except Exception as e:
        print(f"❌ Error during transcription: {e}")
        return ""


def speech_to_text(audio_file: Optional[str] = None, duration: Optional[int] = None) -> str:
    """
    Record audio and convert to text (convenience function)

    Args:
        audio_file: Path to existing audio file (if None, will record new audio)
        duration: Recording duration in seconds (only used if audio_file is None)

    Returns:
        str: Transcribed text or fallback text input
    """
    model = get_whisper_model()
    if not model:
        print("⚠️ Failed to initialize speech recognition model. Falling back to text input.")
        return input("Your answer: ")

    # If no audio file is passed, record audio
    if not audio_file:
        print("🎙️ Recording audio...")
        audio_file = record_audio(duration=duration if duration else 30)

    # Transcribe audio
    print("📝 Transcribing your answer...")
    transcript = transcribe_audio(audio_file, model)

    if not transcript:
        print("⚠️ Transcription failed. Falling back to text input.")
        return input("Your answer: ")

    print(f"✅ Transcribed text: {transcript}")
    return transcript


# ============================================================================
# Text-to-Speech (TTS) Functions
# ============================================================================

# Global TTS pipeline instance
_tts_pipeline: Optional[KPipeline] = None


def initialize_tts_model(lang_code: str = 'a', voice: str = 'af_heart') -> Optional[KPipeline]:
    """
    Initialize the Kokoro TTS model

    Args:
        lang_code: Language code for TTS
        voice: Voice ID to use

    Returns:
        KPipeline instance or None if initialization fails
    """
    global _tts_pipeline
    try:
        _tts_pipeline = KPipeline(lang_code=lang_code)
        print(f"✅ TTS model initialized with voice: {voice}")
        return _tts_pipeline
    except Exception as e:
        print(f"❌ Error initializing TTS model: {e}")
        return None


def get_tts_pipeline() -> Optional[KPipeline]:
    """
    Get the global TTS pipeline instance, initializing if needed

    Returns:
        KPipeline instance or None
    """
    global _tts_pipeline
    if _tts_pipeline is None:
        _tts_pipeline = initialize_tts_model()
    return _tts_pipeline


def text_to_speech(text: str, output_file: Optional[str] = None,
                   voice: str = 'af_heart') -> Optional[str]:
    """
    Convert text to speech using Kokoro TTS

    Args:
        text: Text to convert to speech
        output_file: Path to save audio file (creates temp file if None)
        voice: Voice ID to use

    Returns:
        str: Path to the generated audio file or None if generation fails
    """
    pipeline = get_tts_pipeline()

    if pipeline is None:
        print("❌ Failed to initialize TTS model")
        return None

    try:
        # Create temp file if no output file is specified
        if output_file is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            output_file = temp_file.name
            temp_file.close()

        # Generate audio
        generated = False
        for i, (gs, ps, audio) in enumerate(pipeline(text, voice=voice)):
            if i == 0:  # We only need the first segment for simplicity
                sf.write(output_file, audio, 24000)
                generated = True
                break

        if generated:
            print(f"✅ Audio generated: {output_file}")
            return output_file
        else:
            print("❌ No audio was generated")
            return None

    except Exception as e:
        print(f"❌ Error in text_to_speech: {e}")
        return None


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # STT functions
    'initialize_whisper_model',
    'get_whisper_model',
    'record_audio',
    'transcribe_audio',
    'speech_to_text',
    # TTS functions
    'initialize_tts_model',
    'get_tts_pipeline',
    'text_to_speech',
]


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    print("Testing speech processing module...")
    print("\n1. Testing Speech-to-Text:")
    text = speech_to_text()
    print(f"Final transcription: {text}")

    print("\n2. Testing Text-to-Speech:")
    audio_file = text_to_speech("Hello, this is a test of the text to speech system.")
    if audio_file:
        print(f"Audio saved to: {audio_file}")
