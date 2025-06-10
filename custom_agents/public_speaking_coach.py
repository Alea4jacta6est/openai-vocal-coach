import json
from pydantic import BaseModel
from agents import Agent, function_tool
from typing import List
import yaml


class PublicSpeakingResponse(BaseModel):
    speech_type: str
    goals: List[str]
    structure: List[str]
    rhetorical_devices: List[str]
    body_language: List[str]
    practice_exercises: List[str]
    human_readable_response: str


@function_tool
def get_speaking_guidance(speech_type: str, goals: List[str]) -> dict:
    """Return structured guidance for public speaking based on speech type and goals."""
    # This would typically connect to a database of speaking techniques
    # For now, returning a structured response
    return {
        "speech_type": speech_type,
        "goals": goals,
        "structure": [
            "Strong opening hook",
            "Clear main points with supporting evidence",
            "Compelling conclusion with call to action",
        ],
        "rhetorical_devices": [
            "Anaphora for emphasis",
            "Metaphors for clarity",
            "Rule of three for impact",
        ],
        "body_language": [
            "Confident posture and stance",
            "Purposeful hand gestures",
            "Eye contact with audience",
        ],
        "practice_exercises": [
            "Record and review delivery",
            "Practice with varied pacing",
            "Rehearse with different audience sizes",
        ],
    }


def _load_prompt(fname="prompts/public_speaking_coach_prompt.yml") -> str:
    with open(fname, "r") as fh:
        content = yaml.safe_load(fh)
        return content["template"], content["model_name"]


system_prompt, model_name = _load_prompt()

public_speaking_agent = Agent(
    name="PublicSpeakingCoach",
    instructions=system_prompt,
    model=model_name,
    # tools=[get_speaking_guidance],
    # output_type=PublicSpeakingResponse,
)
