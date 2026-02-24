"""Audio format conversion and processing utilities"""

import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Tuple, BinaryIO
import numpy as np
import librosa
import soundfile as sf

from app.config import config
from app.utils.metrics import record_processing_error

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handle audio format conversion and processing via ffmpeg"""

    # Supported formats mapping to MIME types
    FORMAT_MIME_MAP = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "webm": "audio/webm",
        "ogg": "audio/ogg",
    }

    @staticmethod
    def validate_audio_format(filename: str) -> bool:
        """Check if audio format is supported"""
        ext = Path(filename).suffix.lstrip(".").lower()
        return ext in config.supported_audio_formats

    @staticmethod
    def get_audio_duration(audio_data: bytes, format: str) -> float:
        """Get duration of audio in seconds using librosa"""
        try:
            with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            # Load audio and get duration
            y, sr = librosa.load(tmp_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)

            # Cleanup
            Path(tmp_path).unlink()
            return float(duration)
        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")
            record_processing_error("audio_processor", "duration_extraction")
            raise

    @staticmethod
    def convert_to_wav(
        audio_data: bytes, input_format: str, target_sample_rate: int = 16000
    ) -> Tuple[bytes, int]:
        """
        Convert audio to WAV format with specified sample rate
        Returns: (wav_bytes, actual_sample_rate)
        """
        try:
            # Save input to temporary file
            with tempfile.NamedTemporaryFile(
                suffix=f".{input_format}", delete=False
            ) as input_tmp:
                input_tmp.write(audio_data)
                input_path = input_tmp.name

            # Create output temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output_tmp:
                output_path = output_tmp.name

            # Use ffmpeg to convert
            cmd = [
                "ffmpeg",
                "-i",
                input_path,
                "-acodec",
                "pcm_s16le",
                "-ar",
                str(target_sample_rate),
                "-y",
                output_path,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"ffmpeg conversion failed: {result.stderr}"
                )

            # Read converted audio
            with open(output_path, "rb") as f:
                wav_data = f.read()

            # Cleanup
            Path(input_path).unlink()
            Path(output_path).unlink()

            return wav_data, target_sample_rate

        except subprocess.TimeoutExpired:
            logger.error("Audio conversion timeout")
            record_processing_error("audio_processor", "conversion_timeout")
            raise
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            record_processing_error("audio_processor", "conversion_failed")
            raise

    @staticmethod
    def resample_audio(
        audio_data: bytes,
        original_sample_rate: int,
        target_sample_rate: int,
    ) -> bytes:
        """Resample audio using librosa"""
        try:
            if original_sample_rate == target_sample_rate:
                return audio_data

            # Load audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            y, sr = librosa.load(tmp_path, sr=original_sample_rate)

            # Resample
            y_resampled = librosa.resample(y, orig_sr=sr, target_sr=target_sample_rate)

            # Save resampled audio
            output_path = tmp_path.replace(".wav", "_resampled.wav")
            sf.write(output_path, y_resampled, target_sample_rate)

            # Read and return
            with open(output_path, "rb") as f:
                resampled_data = f.read()

            # Cleanup
            Path(tmp_path).unlink()
            Path(output_path).unlink()

            return resampled_data

        except Exception as e:
            logger.error(f"Resampling failed: {e}")
            record_processing_error("audio_processor", "resampling_failed")
            raise

    @staticmethod
    def normalize_audio(audio_data: bytes) -> bytes:
        """Normalize audio amplitude"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            y, sr = librosa.load(tmp_path, sr=None)

            # Normalize to [-1, 1]
            y_norm = np.clip(y / np.max(np.abs(y)), -1.0, 1.0)

            # Save normalized audio
            output_path = tmp_path.replace(".wav", "_normalized.wav")
            sf.write(output_path, y_norm, sr)

            with open(output_path, "rb") as f:
                normalized_data = f.read()

            # Cleanup
            Path(tmp_path).unlink()
            Path(output_path).unlink()

            return normalized_data

        except Exception as e:
            logger.error(f"Audio normalization failed: {e}")
            record_processing_error("audio_processor", "normalization_failed")
            raise

    @staticmethod
    def encode_to_format(
        audio_array: np.ndarray,
        sample_rate: int,
        format: str,
        bitrate: str = "192k",
    ) -> bytes:
        """Encode audio array to specified format"""
        try:
            # Save to temporary WAV
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_tmp:
                wav_path = wav_tmp.name
                sf.write(wav_path, audio_array, sample_rate)

            # Convert to target format
            with tempfile.NamedTemporaryFile(
                suffix=f".{format}", delete=False
            ) as output_tmp:
                output_path = output_tmp.name

            if format == "mp3":
                cmd = [
                    "ffmpeg",
                    "-i",
                    wav_path,
                    "-b:a",
                    bitrate,
                    "-y",
                    output_path,
                ]
            elif format == "wav":
                # Copy WAV file
                cmd = ["cp", wav_path, output_path]
            else:
                cmd = [
                    "ffmpeg",
                    "-i",
                    wav_path,
                    "-y",
                    output_path,
                ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0 and format != "wav":
                raise RuntimeError(f"Format encoding failed: {result.stderr}")

            # Read encoded audio
            with open(output_path, "rb") as f:
                encoded_data = f.read()

            # Cleanup
            Path(wav_path).unlink()
            Path(output_path).unlink()

            return encoded_data

        except Exception as e:
            logger.error(f"Audio encoding to {format} failed: {e}")
            record_processing_error("audio_processor", f"encoding_{format}_failed")
            raise


# Global instance
audio_processor = AudioProcessor()
