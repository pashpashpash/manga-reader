"""Text-to-speech provider abstraction.

The rest of the pipeline only needs one thing from a TTS backend: given a piece
of narration text, return an in-memory MP3 (a ``BytesIO`` seeked to 0). Each
provider below honours that single contract so ``movie_director.py`` can stay
completely backend-agnostic and the two providers behave identically.

Supported providers (selected with ``TTS_PROVIDER`` / ``--tts-provider``):
  - "elevenlabs": the original ElevenLabs streaming convert call.
  - "60db":       60db's non-streaming POST /tts-synthesize endpoint.
"""

import base64
import os
from io import BytesIO

import httpx
from elevenlabs.client import AsyncElevenLabs
from tenacity import retry, stop_after_attempt, wait_exponential


# ElevenLabs's stock "Adam" voice — kept as the historical default.
DEFAULT_ELEVENLABS_VOICE_ID = "pNInz6obpgDQGcFmaJgB"

# 60db caps a single /tts-synthesize request at 5000 characters, so we split
# longer narration on whitespace and concatenate the resulting MP3 bytes (MP3
# frames concatenate cleanly, exactly like the ElevenLabs streaming chunks do).
SIXTYDB_MAX_CHARS = 4500


class TTSProvider:
    """Common interface. ``synthesize`` returns an MP3 ``BytesIO`` at position 0."""

    name = "base"

    async def synthesize(self, text):  # pragma: no cover - interface only
        raise NotImplementedError


class ElevenLabsProvider(TTSProvider):
    name = "elevenlabs"

    def __init__(self, api_key=None, voice_id=None):
        api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY is not set.")
        self.client = AsyncElevenLabs(api_key=api_key)
        self.voice_id = voice_id or os.getenv(
            "ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE_ID
        )

    async def synthesize(self, text):
        buffer = BytesIO()
        # convert() is an async generator that streams raw MP3 bytes.
        async for audio_bytes in self.client.text_to_speech.convert(
            text=text,
            voice_id=self.voice_id,
        ):
            buffer.write(audio_bytes)
        buffer.seek(0)
        return buffer


class SixtyDBProvider(TTSProvider):
    name = "60db"

    def __init__(
        self,
        api_key=None,
        voice_id=None,
        base_url=None,
        output_format="mp3",
        speed=None,
        stability=None,
        similarity=None,
        enhance=None,
    ):
        self.api_key = api_key or os.getenv("SIXTYDB_API_KEY")
        if not self.api_key:
            raise ValueError("SIXTYDB_API_KEY is not set.")
        # Optional — falls back to 60db's system default voice if unset.
        self.voice_id = voice_id or os.getenv("SIXTYDB_VOICE_ID")
        self.base_url = (
            base_url or os.getenv("SIXTYDB_BASE_URL", "https://api.60db.ai")
        ).rstrip("/")
        self.output_format = output_format

        # Voice-tuning knobs map 1:1 to the API body; env vars allow overrides.
        self.speed = _env_float("SIXTYDB_SPEED", speed)
        self.stability = _env_float("SIXTYDB_STABILITY", stability)
        self.similarity = _env_float("SIXTYDB_SIMILARITY", similarity)
        self.enhance = enhance

    def _base_payload(self, text):
        payload = {"text": text, "output_format": self.output_format}
        if self.voice_id:
            payload["voice_id"] = self.voice_id
        if self.speed is not None:
            payload["speed"] = self.speed
        if self.stability is not None:
            payload["stability"] = self.stability
        if self.similarity is not None:
            payload["similarity"] = self.similarity
        if self.enhance is not None:
            payload["enhance"] = self.enhance
        return payload

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _synthesize_one(self, text):
        """Synthesize a single (<=5000 char) chunk and return raw MP3 bytes."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/tts-synthesize",
                json=self._base_payload(text),
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        if not data.get("success", True):
            raise RuntimeError(
                f"60db synthesis failed: {data.get('message', 'unknown error')}"
            )
        audio_base64 = data.get("audio_base64")
        if not audio_base64:
            raise RuntimeError("60db response did not include audio_base64.")
        return base64.b64decode(audio_base64)

    async def synthesize(self, text):
        buffer = BytesIO()
        for chunk in _chunk_text(text, SIXTYDB_MAX_CHARS):
            buffer.write(await self._synthesize_one(chunk))
        buffer.seek(0)
        return buffer


def create_tts_provider(name=None):
    """Factory: resolve a provider name (or TTS_PROVIDER env var) to an instance."""
    name = (name or os.getenv("TTS_PROVIDER") or "elevenlabs").strip().lower()
    if name in ("elevenlabs", "eleven", "11labs", "el"):
        return ElevenLabsProvider()
    if name in ("60db", "sixtydb", "60"):
        return SixtyDBProvider()
    raise ValueError(
        f"Unknown TTS provider '{name}'. Use 'elevenlabs' or '60db'."
    )


def _env_float(var_name, fallback):
    raw = os.getenv(var_name)
    if raw is None or raw == "":
        return fallback
    return float(raw)


def _chunk_text(text, max_chars):
    """Split text into <=max_chars pieces on whitespace boundaries."""
    text = text.strip()
    if len(text) <= max_chars:
        return [text] if text else []

    chunks = []
    current = ""
    for word in text.split():
        candidate = word if not current else f"{current} {word}"
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks
