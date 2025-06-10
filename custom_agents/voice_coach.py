from pydantic import BaseModel
from agents import Agent, function_tool
from typing import List
import yaml


class VoiceCoachResponse(BaseModel):
    goals: List[str]
    challenges: List[str]
    exercises: List[str]
    warm_ups: List[str]
    health_tips: List[str]
    progress_tracking: str
    human_readable_response: str


@function_tool
def get_vocal_exercises(goals: List[str], challenges: List[str]) -> dict:
    """Return vocal exercises and guidance based on user's goals and challenges."""
    # This would typically connect to a database of exercises
    # For now, returning a structured response
    return {
        "goals": goals,
        "challenges": challenges,
        "exercises": [
            "Breath control: Diaphragmatic breathing exercises",
            "Projection: Resonance exercises with 'ng' sound",
            "Articulation: Lip trills and tongue twisters",
        ],
        "warm_ups": [
            "5-minute gentle humming",
            "Lip trills ascending and descending",
            "Tongue stretches and jaw relaxation",
        ],
        "health_tips": [
            "Stay hydrated throughout the day",
            "Take regular vocal rest breaks",
            "Avoid vocal strain and maintain good posture",
        ],
        "progress_tracking": "Record practice sessions and note improvements in breath control and projection",
    }


def _load_prompt(fname="prompts/voice_coach_prompt.yml") -> str:
    with open(fname, "r") as fh:
        content = yaml.safe_load(fh)
        return content["template"], content["model_name"]


system_prompt, model_name = _load_prompt()

voice_coach_agent = Agent(
    name="VoiceCoach",
    instructions=system_prompt,
    model=model_name,
    tools=[get_vocal_exercises],
    output_type=VoiceCoachResponse,
)
