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
            "Articulation: Lip trills and tongue twisters"
        ],
        "warm_ups": [
            "5-minute gentle humming",
            "Lip trills ascending and descending",
            "Tongue stretches and jaw relaxation"
        ],
        "health_tips": [
            "Stay hydrated throughout the day",
            "Take regular vocal rest breaks",
            "Avoid vocal strain and maintain good posture"
        ],
        "progress_tracking": "Record practice sessions and note improvements in breath control and projection"
    }


def _load_prompt_template() -> str:
    with open("prompts/voice_coach_prompt.yml", "r") as fh:
        return yaml.safe_load(fh)["template"]


VOICE_COACH_PROMPT_TEMPLATE: str = _load_prompt_template()

voice_coach_agent = Agent(
    name="VoiceCoach",
    instructions=VOICE_COACH_PROMPT_TEMPLATE,
    model="gpt-4o-mini",
    tools=[get_vocal_exercises],
    output_type=VoiceCoachResponse
)
