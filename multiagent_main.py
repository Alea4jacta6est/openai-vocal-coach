import asyncio
from agents import Agent, Runner, function_tool
from dotenv import load_dotenv
load_dotenv()

from custom_agents.dialect_coach import dialect_agent
from custom_agents.public_speaking_coach import public_speaking_agent
from custom_agents.voice_coach import voice_coach_agent
from custom_agents.triage_agent import triage_agent

AGENT_MAP = {
    "dialect_coach": dialect_agent,
    "public_speaking_coach": public_speaking_agent,
    "voice_coach": voice_coach_agent
}

async def main():
    print("Welcome to the Multi-Agent Coaching System!")
    print("You can ask about dialect training, public speaking, or voice coaching.")
    print("Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
            
        triage_result = await Runner.run(triage_agent, user_input)
        selected_agent_name = triage_result.final_output.selected_agent
        selected_agent = AGENT_MAP[selected_agent_name]
        
        print(f"\nSelected agent: {selected_agent_name}")
        print(f"Reasoning: {triage_result.final_output.reasoning}")
        
        # Now run the selected agent with the user's input
        result = await Runner.run(selected_agent, user_input)
        
        print(f"\nResponse: {result.final_output}")

if __name__ == "__main__":
    asyncio.run(main())