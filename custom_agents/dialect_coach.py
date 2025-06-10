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
            "reason": f"No tongue twisters found for {language}."
        }
    selected = tws[:6]
    reason = (
       f"I selected these {language} tongue twisters because they help with: {improvements}."
    )
    return {"language": language, "improvements": improvements, "twisters": selected, "reason": reason}

def _load_prompt_template() -> str:
    with open("prompts/dialect_coach_prompt.yml", "r") as fh:
        return yaml.safe_load(fh)["template"]

DIALECT_PROMPT_TEMPLATE: str = _load_prompt_template()

dialect_agent = Agent(
    name="DialectCoach",
    instructions=DIALECT_PROMPT_TEMPLATE,
    model="gpt-4o-mini",
    tools=[get_twisters],
    output_type=TwisterResponse
)