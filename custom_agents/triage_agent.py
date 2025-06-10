from pydantic import BaseModel
from agents import Agent, Runner, function_tool


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
    
    if any(word in input_lower for word in ["tongue", "twister", "dialect", "accent", "pronunciation"]):
        return {
            "selected_agent": "dialect_coach",
            "confidence": 0.9,
            "reasoning": "User is asking about dialect or pronunciation practice"
        }
    elif any(word in input_lower for word in ["speech", "presentation", "pitch", "talk", "speaking"]):
        return {
            "selected_agent": "public_speaking_coach",
            "confidence": 0.9,
            "reasoning": "User is asking about public speaking or presentations"
        }
    elif any(word in input_lower for word in ["voice", "vocal", "singing", "breathing"]):
        return {
            "selected_agent": "voice_coach",
            "confidence": 0.9,
            "reasoning": "User is asking about voice training or vocal exercises"
        }
    else:
        return {
            "selected_agent": "public_speaking_coach",
            "confidence": 0.5,
            "reasoning": "Defaulting to public speaking coach as it's the most general-purpose agent"
        }

triage_agent = Agent(
    name="TriageAgent",
    instructions="""You are a triage agent that helps route user requests to the most appropriate specialized agent.
    You have access to three specialized agents:
    1. Dialect Coach ("dialect_coach") - For pronunciation, accent training, and tongue twisters
    2. Public Speaking Coach ("public_speaking_coach") - For speech preparation, presentation skills, and public speaking
    3. Voice Coach ("voice_coach") - For vocal training, breathing exercises, and voice improvement
    
    Analyze the user's input and select the most appropriate agent to handle their request, returning only one of these strings:
    dialect_coach
    public_speaking_coach
    voice_coach
    """,
    model="gpt-4o-mini", 
    tools=[select_agent],
    output_type=AgentResponse
)