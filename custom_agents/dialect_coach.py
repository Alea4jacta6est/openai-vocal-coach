import json
from pydantic import BaseModel
from agents import Agent, function_tool
from typing import List, Callable
import yaml


class TwisterResponse(BaseModel):
    language: str
    improvements: str
    twisters: List[str]
    reason: str
    human_readable_response: str


with open("data/tongue_twisters.json", encoding="utf-8") as f:
    TW_DB = json.load(f)


@function_tool
def get_twisters(language: str, improvements: str) -> dict:
    """Return 3 tongue twisters and a reason for choosing them, given a language and improvement goal."""
    tws = TW_DB.get(language, [])
    if not tws:
        return {
            "language": language,
            "improvements": improvements,
            "twisters": [],
            "reason": f"No tongue twisters found for {language}.",
        }
    selected = tws[:6]
    reason = f"I selected these {language} tongue twisters because they help with: {improvements}."
    return {
        "language": language,
        "improvements": improvements,
        "twisters": selected,
        "reason": reason,
    }


def _load_prompt(fname="prompts/dialect_coach_prompt.yml") -> str:
    with open(fname, "r") as fh:
        content = yaml.safe_load(fh)
        return content["template"], content["model_name"]


system_prompt, model_name = _load_prompt()

dialect_agent = Agent(
    name="DialectCoach",
    instructions=system_prompt,
    model=model_name,
    tools=[get_twisters],
    output_type=TwisterResponse,
)
