from pydantic import BaseModel
from agents import Agent, Runner, function_tool
import yaml


class AgentResponse(BaseModel):
    selected_agent: str
    confidence: float
    reasoning: str


@function_tool
def select_agent(user_input: str) -> dict:
    """Select the most appropriate agent based on the user's input."""
    # This would typically use a more sophisticated selection mechanism
    # For now, using simple keyword matching
    input_lower = user_input.lower()

    if any(
        word in input_lower
        for word in ["tongue", "twister", "dialect", "accent", "pronunciation"]
    ):
        return {
            "selected_agent": "dialect_coach",
            "confidence": 0.9,
            "reasoning": "User is asking about dialect or pronunciation practice",
        }
    elif any(
        word in input_lower
        for word in ["speech", "presentation", "pitch", "talk", "speaking"]
    ):
        return {
            "selected_agent": "public_speaking_coach",
            "confidence": 0.9,
            "reasoning": "User is asking about public speaking or presentations",
        }
    elif any(
        word in input_lower for word in ["voice", "vocal", "singing", "breathing"]
    ):
        return {
            "selected_agent": "voice_coach",
            "confidence": 0.9,
            "reasoning": "User is asking about voice training or vocal exercises",
        }
    else:
        return {
            "selected_agent": "public_speaking_coach",
            "confidence": 0.5,
            "reasoning": "Defaulting to public speaking coach as it's the most general-purpose agent",
        }


def _load_prompt(fname="prompts/triage_agent_prompt.yml") -> str:
    with open(fname, "r") as fh:
        content = yaml.safe_load(fh)
        return content["template"], content["model_name"]


system_prompt, model_name = _load_prompt()

triage_agent = Agent(
    name="TriageAgent",
    instructions=system_prompt,
    model=model_name,
    tools=[select_agent],
    output_type=AgentResponse,
)
