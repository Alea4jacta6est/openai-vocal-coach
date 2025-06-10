"""
Multi-Agent Coaching System — Gradio ChatInterface
"""

import os
import time
import asyncio

import gradio as gr
from gradio import ChatMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents import Runner
from custom_agents.dialect_coach import dialect_agent
from custom_agents.public_speaking_coach import public_speaking_agent
from custom_agents.voice_coach import voice_coach_agent
from custom_agents.triage_agent import triage_agent

AGENT_MAP = {
    "dialect_coach": dialect_agent,
    "public_speaking_coach": public_speaking_agent,
    "voice_coach": voice_coach_agent,
}


async def coach_chat(message: str, history: list[dict]):
    """Route the message through triage → specialist and stream thoughts."""

    # 1️⃣ Triage (intermediate thought)
    triage_chat = ChatMessage(
        content="",
        metadata={"title": "🔍 Triage & Tool Selection", "id": 0, "status": "pending"},
    )
    start = time.time()
    yield triage_chat

    triage_result = await Runner.run(triage_agent, message)
    selected_agent_name = triage_result.final_output.selected_agent
    reasoning = triage_result.final_output.reasoning

    triage_chat.content = (
        f"**Reasoning**\n{reasoning}\n\n"
        f"**Chosen coach:** {selected_agent_name.replace('_', ' ').title()}"
    )
    triage_chat.metadata["status"] = "done"
    triage_chat.metadata["duration"] = round(time.time() - start, 2)
    yield triage_chat

    # 2️⃣ Specialist response
    coach = AGENT_MAP[selected_agent_name]
    coach_result = await Runner.run(coach, message)
    reply = coach_result.final_output

    yield reply


demo = gr.ChatInterface(
    fn=coach_chat,
    type="messages",
    theme="soft",
    title="🗣️ Multi-Agent Coaching System",
    description=(
        "Ask anything about dialect training, public speaking, or voice coaching. "
        "The system will show its reasoning and the tool it picks before replying."
    ),
    examples=[
        "How can I reduce my accent when pronouncing 'th'?",
        "Tips for conquering stage fright during presentations?",
        "How do I improve my vocal projection without straining?",
    ],
    save_history=True,
    flagging_mode="manual",
    flagging_options=["Like", "Dislike", "Spam", "Other"],
)

if __name__ == "__main__":
    demo.queue()
    demo.launch(server_name="0.0.0.0", show_api=False)
