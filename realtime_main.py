from __future__ import annotations

"""Multi-Agent Voice Assistant App

This app combines the existing multi-agent coaching system with a voice-first
Textual UI. It lets you speak a request, routes the transcription through your
triage agent to pick the right specialist coach, streams the chosen coach’s
response back as synthesised audio, and shows the full conversation in a Rich
log panel.

Controls:
  K   Toggle microphone recording on/off
  Q   Quit the application

Environment variables should live in an `.env` file and include whatever API
keys or settings your speech and agent services need.
"""

import asyncio
from typing import TYPE_CHECKING

import numpy as np
import sounddevice as sd
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import RichLog, Static
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load env vars (OpenAI keys etc.)
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Your existing agents
# ---------------------------------------------------------------------------
from agents import Runner  # type: ignore
from custom_agents.dialect_coach import dialect_agent  # type: ignore
from custom_agents.public_speaking_coach import public_speaking_agent  # type: ignore
from custom_agents.voice_coach import voice_coach_agent  # type: ignore
from custom_agents.triage_agent import triage_agent  # type: ignore

# ---------------------------------------------------------------------------
# Voice pipeline pieces
# ---------------------------------------------------------------------------
from agents.voice import StreamedAudioInput, VoicePipeline  # type: ignore
from workflows.my_workflow import MyWorkflow  # type: ignore

# ---------------------------------------------------------------------------
# Audio constants
# ---------------------------------------------------------------------------
CHUNK_LENGTH_S = 0.05  # 50 ms
SAMPLE_RATE = 24_000
FORMAT = np.int16
CHANNELS = 1

# Mapping from triage key → specialised agent
AGENT_MAP = {
    "dialect_coach": dialect_agent,
    "public_speaking_coach": public_speaking_agent,
    "voice_coach": voice_coach_agent,
}

# =============================================================================
#                               UI widgets
# =============================================================================

class Header(Static):
    session_id: reactive[str] = reactive("")

    def render(self) -> str:  # type: ignore[override]
        return "🎙  Speak to your Multi-Agent Coach   (K = record, Q = quit)"


class AudioStatusIndicator(Static):
    is_recording: reactive[bool] = reactive(False)

    def render(self) -> str:  # type: ignore[override]
        return "🔴 Recording… (K to stop)" if self.is_recording else "⚪ Idle. Press K to record"


# =============================================================================
#                             Main Application
# =============================================================================

class CoachingApp(App[None]):
    """Voice-first interface to the agent ecosystem."""

    CSS = """
    Screen { background: #1a1b26; }
    Container { border: double rgb(91,164,91); }
    #bottom-pane { width: 100%; height: 90%; border: round rgb(205,133,63); padding: 1; }
    #status-indicator { height: 3; content-align: center middle; background: #2a2b36; }
    Static { color: white; }
    """

    def __init__(self) -> None:
        super().__init__()

        # Mic input stream + audio out
        self._audio_input = StreamedAudioInput()
        self.audio_player = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=FORMAT,
        )

        # Event used by key-toggle to gate sending mic chunks
        self.should_send_audio = asyncio.Event()

        # Voice pipeline = STT → callback → TTS
        self.pipeline = VoicePipeline(
            workflow=MyWorkflow(secret_word="dog", on_start=self._on_transcription)
        )

    # -------------------- UI layout --------------------

    def compose(self) -> ComposeResult:  # type: ignore[override]
        with Container():
            yield Header(id="header")
            yield AudioStatusIndicator(id="status-indicator")
            yield RichLog(id="bottom-pane", wrap=True, highlight=True, markup=True)

    async def on_mount(self) -> None:  # type: ignore[override]
        self.run_worker(self._start_voice_pipeline())
        self.run_worker(self._capture_mic_audio())

    # ==================================================
    # Worker: Capture microphone audio
    # ==================================================

    async def _capture_mic_audio(self) -> None:
        read_size = int(SAMPLE_RATE * CHUNK_LENGTH_S)
        stream = sd.InputStream(
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            dtype=FORMAT,
        )
        stream.start()

        status = self.query_one(AudioStatusIndicator)

        try:
            while True:
                if not self.should_send_audio.is_set():
                    status.is_recording = False
                    await asyncio.sleep(0.05)
                    continue

                status.is_recording = True

                if stream.read_available < read_size:
                    await asyncio.sleep(0.0)
                    continue

                data, _ = stream.read(read_size)
                await self._audio_input.add_audio(data)
        except asyncio.CancelledError:
            pass
        finally:
            stream.stop(); stream.close(); status.is_recording = False

    # ==================================================
    # Worker: Listen to pipeline events (audio + lifecycle)
    # ==================================================

    async def _start_voice_pipeline(self) -> None:
        bottom_pane = self.query_one("#bottom-pane", RichLog)
        try:
            self.audio_player.start()
            pipeline_result = await self.pipeline.run(self._audio_input)
            async for event in pipeline_result.stream():
                if event.type == "voice_stream_event_audio":
                    # Fix: event.data is a NumPy array – checking its truth value directly is ambiguous
                    if event.data is not None and getattr(event.data, "size", 0):
                        self.audio_player.write(event.data)
                elif event.type == "voice_stream_event_lifecycle":
                    bottom_pane.write(f"[italic cyan]• Pipeline:[/] {event.event}")
        except Exception as exc:  # noqa: BLE001
            bottom_pane.write(f"[red]Voice pipeline error:[/] {exc}")
        finally:
            self.audio_player.close()

    # ==================================================
    # Callback: Finalised transcription ready
    # ==================================================

    async def _on_transcription(self, transcription: str) -> None:
        bottom_pane = self.query_one("#bottom-pane", RichLog)
        bottom_pane.write(f"[bold yellow]You:[/] {transcription}")

        # 1️⃣  Triage → pick coach
        triage_result = await Runner.run(triage_agent, transcription)
        agent_key = triage_result.final_output.selected_agent
        bottom_pane.write(
            f"[italic cyan]• Triage selected:[/] {agent_key} — {triage_result.final_output.reasoning}"
        )

        # 2️⃣  Get coach reply
        agent = AGENT_MAP[agent_key]
        agent_result = await Runner.run(agent, transcription)
        assistant_reply = agent_result.final_output
        bottom_pane.write(f"[bold green]{agent_key.replace('_', ' ').title()}:[/] {assistant_reply}")

        # 3️⃣  Speak reply (if VoicePipeline exposes TTS method)
        speak = getattr(self.pipeline, "say", None)
        if callable(speak):
            await speak(assistant_reply)  # type: ignore[arg-type]
        else:
            bottom_pane.write("[red]⚠️  No TTS capability in VoicePipeline.[/]")

    # -------------------- Keybindings --------------------

    async def on_key(self, event: events.Key) -> None:  # type: ignore[override]
        if event.key == "q":
            self.exit(); return
        if event.key == "k":
            # Toggle mic recording
            if self.should_send_audio.is_set():
                self.should_send_audio.clear()
            else:
                self.should_send_audio.set()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    CoachingApp().run()
