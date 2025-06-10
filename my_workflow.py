import random
import json
from collections.abc import AsyncIterator
from pydantic import BaseModel
from typing import List, Callable
from dotenv import load_dotenv

from agents import Agent, Runner, TResponseInputItem, function_tool, OpenAIChatCompletionsModel
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from agents.voice import VoiceWorkflowBase, VoiceWorkflowHelper

load_dotenv()

#openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class TwisterResponse(BaseModel):
    language: str
    improvements: str
    twisters: List[str]
    reason: str


with open("data/tongue_twisters.json", encoding="utf-8") as f:
    TW_DB = json.load(f)


@function_tool
def get_twisters(language: str, improvements: str) -> dict:
    """Return 5–6 tongue twisters and a reason for choosing them, given a language and improvement goal."""
    tws = TW_DB.get(language, [])
    if not tws:
        return {
            "language": language,
            "improvements": improvements,
            "twisters": [],
            "reason": f"No tongue twisters found for {language}."
        }
    selected = tws[:6]
    #reason = (
    #    f"I selected these {language} tongue twisters because they help with: {improvements}."
    #)
    return {"language": language, "improvements": improvements, "twisters": selected, "reason": reason}


agent = Agent(
    name="PublicSpeakingCoach",
    instructions="""
You are a public speaking coach.
Given a user message that includes feedback on their pitch or speech:
1. Detect the language they were speaking in.
2. Identify the improvement goals provided in context (e.g. reduce filler words, slow down, improve articulation).
3. Call the get_twisters tool with the language and improvement.
Return the tool output (language, twisters, reason) as plain JSON.
""",
    model="gpt-4o-mini", #, openai_client=openai_client
    tools=[get_twisters],
    output_type=TwisterResponse
)


class MyWorkflow(VoiceWorkflowBase):
    def __init__(self, secret_word: str, on_start: Callable[[str], None]):
        """
        Args:
            secret_word: The secret word to guess.
            on_start: A callback that is called when the workflow starts. The transcription
                is passed in as an argument.
        """
        self._input_history: list[TResponseInputItem] = []
        self._current_agent = agent
        self._secret_word = secret_word.lower()
        self._on_start = on_start

    async def run(self, transcription: str) -> AsyncIterator[str]:
        self._on_start(transcription)

        # Add the transcription to the input history
        self._input_history.append(
            {
                "role": "user",
                "content": transcription,
            }
        )

        # If the user guessed the secret word, do alternate logic
        if self._secret_word in transcription.lower():
            yield "You guessed the secret word!"
            self._input_history.append(
                {
                    "role": "assistant",
                    "content": "You guessed the secret word!",
                }
            )
            return

        # Otherwise, run the agent
        result = Runner.run_streamed(self._current_agent, self._input_history)

        async for chunk in VoiceWorkflowHelper.stream_text_from(result):
            yield chunk

        # Update the input history and current agent
        self._input_history = result.to_input_list()
        self._current_agent = result.last_agent
