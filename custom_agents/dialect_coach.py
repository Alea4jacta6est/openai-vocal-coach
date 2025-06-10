import json
from pydantic import BaseModel
from agents import Agent, function_tool
from typing import List, Callable
import yaml
from gradio import ChatMessage


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

# dialect_agent = Agent(
#     name="DialectCoach",
#     instructions=system_prompt,
#     model=model_name,
#     tools=[get_twisters],
#     output_type=TwisterResponse,
# )
# dialect_agent.py  (only the new code is shown)
from gradio import ChatMessage
from agents import Agent, function_tool


class DialectAgent(Agent):
    async def run(self, user_message: str):
        """Runs the normal Agent logic, then converts the Pydantic
        model to a ChatMessage so Gradio is happy."""
        run = await super().run(user_message)

        # The model you declared in output_type
        tw: TwisterResponse = run.final_output

        run.final_output = ChatMessage(
            content=tw.human_readable_response,
            metadata={
                "language": tw.language,
                "improvements": tw.improvements,
                "twisters": tw.twisters,
                "reason": tw.reason,
            },
        )
        return run


dialect_agent = DialectAgent(
    name="DialectCoach",
    instructions=system_prompt,
    model=model_name,
    tools=[get_twisters],
    # output_type=TwisterResponse,   # keep it – we still parse JSON
)
